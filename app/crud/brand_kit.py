from typing import Optional, Dict, Any, List
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


def _pain_points_to_list(value: Any) -> List[str]:
    """
    Normalise customer_pain_points coming out of the database.

    The onboarding service writes this column as a newline-separated TEXT
    string.  Future API writes may pass a JSON array (JSONB) or a plain list.
    Always return List[str] so the Pydantic response model is satisfied.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [p.strip() for p in value.split("\n") if p.strip()]
    return []


def _pain_points_to_str(value: Any) -> str:
    """
    Serialise customer_pain_points for writing to the TEXT column.

    Accepts either a list (from the API) or a string (passthrough).
    Returns a newline-separated string consistent with what the onboarding
    service writes.
    """
    if isinstance(value, list):
        return "\n".join(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, str):
        return value.strip()
    return ""


def _normalize_brand_kit(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *record* with customer_pain_points coerced to List[str]."""
    result = dict(record)
    result["customer_pain_points"] = _pain_points_to_list(result.get("customer_pain_points"))
    return result


def _prepare_brand_kit_write(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *data* with customer_pain_points serialised for the TEXT column."""
    result = dict(data)
    if "customer_pain_points" in result:
        result["customer_pain_points"] = _pain_points_to_str(result["customer_pain_points"])
    return result


class CRUDBrandKit(CRUDBase):
    """CRUD operations for brand_kits table."""

    def __init__(self):
        super().__init__("brand_kits")

    async def get_by_user(
        self,
        supabase: Client,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the brand kit for a specific user (users have at most one)."""
        try:
            response = (
                supabase.table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                return None

            return _normalize_brand_kit(response.data[0])

        except Exception as e:
            logger.error(f"Error getting brand kit for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get brand kit",
            )

    async def create(
        self,
        supabase: Client,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a brand kit, normalising customer_pain_points for the TEXT column."""
        result = await super().create(supabase, _prepare_brand_kit_write(data), user_id)
        return _normalize_brand_kit(result)

    async def update(
        self,
        supabase: Client,
        id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a brand kit, normalising customer_pain_points for the TEXT column."""
        result = await super().update(supabase, id, _prepare_brand_kit_write(data), user_id)
        return _normalize_brand_kit(result)

    async def create_or_update_for_user(
        self,
        supabase: Client,
        user_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create or update the brand kit for a user."""
        existing = await self.get_by_user(supabase, user_id)

        if existing:
            return await self.update(supabase, existing["id"], data, user_id)
        else:
            return await self.create(supabase, data, user_id)


# Singleton instance
brand_kit_crud = CRUDBrandKit()
