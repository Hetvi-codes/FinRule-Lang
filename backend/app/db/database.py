import os
import json
import uuid
import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings


class LocalJSONStore:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.collections = ["users", "projects", "models", "versions", "executions", "custom_templates"]
        self._ensure_files()

    def _get_path(self, collection: str) -> str:
        return os.path.join(self.data_dir, f"{collection}.json")

    def _ensure_files(self):
        for col in self.collections:
            path = self._get_path(col)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f)

    def _read(self, collection: str) -> List[Dict[str, Any]]:
        path = self._get_path(collection)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, collection: str, data: List[Dict[str, Any]]):
        path = self._get_path(collection)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    # Generic CRUD
    async def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = self._read(collection)
        matched = []
        for item in items:
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                matched.append(item)
        return matched

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        results = await self.find(collection, query)
        return results[0] if results else None

    async def insert_one(self, collection: str, doc: Dict[str, Any]) -> str:
        items = self._read(collection)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        if "created_at" not in doc:
            doc["created_at"] = datetime.datetime.utcnow().isoformat()
        if "updated_at" not in doc:
            doc["updated_at"] = doc["created_at"]
        items.append(doc)
        self._write(collection, items)
        return doc["_id"]

    async def update_one(self, collection: str, query: Dict[str, Any], updates: Dict[str, Any]) -> bool:
        items = self._read(collection)
        for i, item in enumerate(items):
            match = True
            for k, v in query.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                items[i].update(updates)
                items[i]["updated_at"] = datetime.datetime.utcnow().isoformat()
                self._write(collection, items)
                return True
        return False

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        items = self._read(collection)
        initial_len = len(items)
        items = [item for item in items if not all(item.get(k) == v for k, v in query.items())]
        if len(items) != initial_len:
            self._write(collection, items)
            return True
        return False


def _prepare_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" not in doc:
        doc["_id"] = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    if "created_at" not in doc:
        doc["created_at"] = now
    if "updated_at" not in doc:
        doc["updated_at"] = doc["created_at"]
    return doc


def _id_query(doc_id: str) -> Any:
    try:
        from bson import ObjectId
        if ObjectId.is_valid(doc_id):
            return {"$in": [doc_id, ObjectId(doc_id)]}
    except Exception:
        pass
    return doc_id


class DatabaseManager:
    def __init__(self):
        self.use_mongo = False
        self.mongo_client: Optional[AsyncIOMotorClient] = None
        self.mongo_db = None
        self.local_store = LocalJSONStore(settings.DATA_DIR)

    async def init_db(self):
        if settings.MONGODB_URI:
            try:
                self.mongo_client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
                await self.mongo_client.server_info()
                self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
                self.use_mongo = True
                print(f"[DB] Successfully connected to MongoDB Atlas: {settings.DATABASE_NAME} (Primary Storage: ACTIVE)")
            except Exception as e:
                print(f"[DB] MongoDB connection failed ({e}). Falling back to Local Storage.")
                self.use_mongo = False
        else:
            print("[DB] No MONGODB_URI set. Using Local JSON Store as primary storage.")

    # Users
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            try:
                doc = await self.mongo_db.users.find_one({"email": email})
                if doc:
                    doc["_id"] = str(doc["_id"])
                    return doc
            except Exception as e:
                print(f"[DB Warning] Mongo get_user_by_email failed ({e}). Using local fallback.")
        return await self.local_store.find_one("users", {"email": email})

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            try:
                doc = await self.mongo_db.users.find_one({"_id": _id_query(user_id)})
                if doc:
                    doc["_id"] = str(doc["_id"])
                    return doc
            except Exception as e:
                print(f"[DB Warning] Mongo get_user_by_id failed ({e}). Using local fallback.")
        return await self.local_store.find_one("users", {"_id": user_id})

    async def create_user(self, user_doc: Dict[str, Any]) -> str:
        _prepare_doc(user_doc)
        if self.use_mongo:
            try:
                res = await self.mongo_db.users.insert_one(user_doc)
                return str(user_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo create_user failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("users", user_doc)

    # Projects
    async def list_projects(self, user_id: str) -> List[Dict[str, Any]]:
        if self.use_mongo:
            try:
                cursor = self.mongo_db.projects.find({"user_id": user_id})
                docs = await cursor.to_list(length=100)
                for d in docs:
                    d["_id"] = str(d["_id"])
                return docs
            except Exception as e:
                print(f"[DB Warning] Mongo list_projects failed ({e}). Using local fallback.")
        return await self.local_store.find("projects", {"user_id": user_id})

    async def create_project(self, project_doc: Dict[str, Any]) -> str:
        _prepare_doc(project_doc)
        if self.use_mongo:
            try:
                await self.mongo_db.projects.insert_one(project_doc)
                return str(project_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo create_project failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("projects", project_doc)

    async def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            try:
                doc = await self.mongo_db.projects.find_one({"_id": _id_query(project_id), "user_id": user_id})
                if doc:
                    doc["_id"] = str(doc["_id"])
                    return doc
            except Exception as e:
                print(f"[DB Warning] Mongo get_project failed ({e}). Using local fallback.")
        return await self.local_store.find_one("projects", {"_id": project_id, "user_id": user_id})

    async def update_project(self, project_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        if self.use_mongo:
            try:
                updates["updated_at"] = datetime.datetime.utcnow().isoformat()
                res = await self.mongo_db.projects.update_one({"_id": _id_query(project_id), "user_id": user_id}, {"$set": updates})
                if res.matched_count > 0:
                    return True
            except Exception as e:
                print(f"[DB Warning] Mongo update_project failed ({e}). Using local fallback.")
        return await self.local_store.update_one("projects", {"_id": project_id, "user_id": user_id}, updates)

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        if self.use_mongo:
            try:
                await self.mongo_db.models.delete_many({"project_id": project_id, "user_id": user_id})
                res = await self.mongo_db.projects.delete_one({"_id": _id_query(project_id), "user_id": user_id})
                return res.deleted_count > 0
            except Exception as e:
                print(f"[DB Warning] Mongo delete_project failed ({e}). Using local fallback.")
        models = await self.local_store.find("models", {"project_id": project_id, "user_id": user_id})
        for m in models:
            await self.local_store.delete_one("models", {"_id": m["_id"]})
        return await self.local_store.delete_one("projects", {"_id": project_id, "user_id": user_id})

    # Models
    async def list_models(self, project_id: str, user_id: str) -> List[Dict[str, Any]]:
        if self.use_mongo:
            try:
                cursor = self.mongo_db.models.find({"project_id": project_id, "user_id": user_id})
                docs = await cursor.to_list(length=100)
                for d in docs:
                    d["_id"] = str(d["_id"])
                return docs
            except Exception as e:
                print(f"[DB Warning] Mongo list_models failed ({e}). Using local fallback.")
        return await self.local_store.find("models", {"project_id": project_id, "user_id": user_id})

    async def create_model(self, model_doc: Dict[str, Any]) -> str:
        _prepare_doc(model_doc)
        if self.use_mongo:
            try:
                await self.mongo_db.models.insert_one(model_doc)
                return str(model_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo create_model failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("models", model_doc)

    async def get_model(self, model_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            try:
                doc = await self.mongo_db.models.find_one({"_id": _id_query(model_id), "user_id": user_id})
                if doc:
                    doc["_id"] = str(doc["_id"])
                    return doc
            except Exception as e:
                print(f"[DB Warning] Mongo get_model failed ({e}). Using local fallback.")
        return await self.local_store.find_one("models", {"_id": model_id, "user_id": user_id})

    async def update_model(self, model_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        if self.use_mongo:
            try:
                updates["updated_at"] = datetime.datetime.utcnow().isoformat()
                res = await self.mongo_db.models.update_one({"_id": _id_query(model_id), "user_id": user_id}, {"$set": updates})
                if res.matched_count > 0:
                    return True
            except Exception as e:
                print(f"[DB Warning] Mongo update_model failed ({e}). Using local fallback.")
        return await self.local_store.update_one("models", {"_id": model_id, "user_id": user_id}, updates)

    async def delete_model(self, model_id: str, user_id: str) -> bool:
        if self.use_mongo:
            try:
                res = await self.mongo_db.models.delete_one({"_id": _id_query(model_id), "user_id": user_id})
                return res.deleted_count > 0
            except Exception as e:
                print(f"[DB Warning] Mongo delete_model failed ({e}). Using local fallback.")
        return await self.local_store.delete_one("models", {"_id": model_id, "user_id": user_id})

    # Versions
    async def add_version(self, version_doc: Dict[str, Any]) -> str:
        _prepare_doc(version_doc)
        if self.use_mongo:
            try:
                await self.mongo_db.versions.insert_one(version_doc)
                return str(version_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo add_version failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("versions", version_doc)

    async def list_versions(self, model_id: str) -> List[Dict[str, Any]]:
        if self.use_mongo:
            try:
                cursor = self.mongo_db.versions.find({"model_id": model_id}).sort("created_at", -1)
                docs = await cursor.to_list(length=50)
                for d in docs:
                    d["_id"] = str(d["_id"])
                return docs
            except Exception as e:
                print(f"[DB Warning] Mongo list_versions failed ({e}). Using local fallback.")
        versions = await self.local_store.find("versions", {"model_id": model_id})
        versions.sort(key=lambda v: v.get("created_at", ""), reverse=True)
        return versions

    # Executions
    async def log_execution(self, exec_doc: Dict[str, Any]) -> str:
        _prepare_doc(exec_doc)
        if self.use_mongo:
            try:
                await self.mongo_db.executions.insert_one(exec_doc)
                return str(exec_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo log_execution failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("executions", exec_doc)

    async def list_executions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.use_mongo:
            try:
                cursor = self.mongo_db.executions.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
                docs = await cursor.to_list(length=limit)
                for d in docs:
                    d["_id"] = str(d["_id"])
                return docs
            except Exception as e:
                print(f"[DB Warning] Mongo list_executions failed ({e}). Using local fallback.")
        items = await self.local_store.find("executions", {"user_id": user_id})
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items[:limit]

    # Custom Templates
    async def list_custom_templates(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"user_id": user_id} if user_id else {}
        if self.use_mongo:
            try:
                cursor = self.mongo_db.custom_templates.find(query).sort("created_at", -1)
                docs = await cursor.to_list(length=100)
                for d in docs:
                    d["_id"] = str(d["_id"])
                return docs
            except Exception as e:
                print(f"[DB Warning] Mongo list_custom_templates failed ({e}). Using local fallback.")
        return await self.local_store.find("custom_templates", query)

    async def create_custom_template(self, template_doc: Dict[str, Any]) -> str:
        _prepare_doc(template_doc)
        if self.use_mongo:
            try:
                await self.mongo_db.custom_templates.insert_one(template_doc)
                return str(template_doc["_id"])
            except Exception as e:
                print(f"[DB Warning] Mongo create_custom_template failed ({e}). Saving to local store.")
        return await self.local_store.insert_one("custom_templates", template_doc)

    async def delete_custom_template(self, template_id: str, user_id: Optional[str] = None) -> bool:
        query = {"_id": _id_query(template_id)}
        if user_id:
            query["user_id"] = user_id
        if self.use_mongo:
            try:
                res = await self.mongo_db.custom_templates.delete_one(query)
                return res.deleted_count > 0
            except Exception as e:
                print(f"[DB Warning] Mongo delete_custom_template failed ({e}). Using local fallback.")
        return await self.local_store.delete_one("custom_templates", {"_id": template_id})


db = DatabaseManager()
