from typing import Generic, TypeVar, Optional, List, Dict, Any
from supabase import Client
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Type variable for generic CRUD operations
ModelType = TypeVar("ModelType")


class CRUDBase(Generic[ModelType]):
    """
    Base class for CRUD operations using Supabase.
    Provides generic create, read, update, delete operations.
    """
    
    def __init__(self, table_name: str):
        """
        Initialize CRUD operations for a specific table.
        
        Args:
            table_name: Name of the Supabase table
        """
        self.table_name = table_name
    
    async def create(
        self, 
        supabase: Client, 
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new record.
        
        Args:
            supabase: Supabase client
            data: Record data as dictionary
            user_id: Optional user_id to add to the record
            
        Returns:
            Created record
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            # Add user_id if provided and not already in data
            if user_id and "user_id" not in data:
                data["user_id"] = user_id
            
            response = supabase.table(self.table_name).insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create {self.table_name}"
            )
    
    async def get(
        self, 
        supabase: Client, 
        id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            supabase: Supabase client
            id: Record ID
            user_id: Optional user_id for user-scoped queries
            
        Returns:
            Record if found, None otherwise
            
        Raises:
            HTTPException: If query fails
        """
        try:
            query = supabase.table(self.table_name).select("*").eq("id", id)
            
            # Add user_id filter if provided
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting {self.table_name} {id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get {self.table_name}"
            )
    
    async def get_or_404(
        self, 
        supabase: Client, 
        id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a record by ID or raise 404.
        
        Args:
            supabase: Supabase client
            id: Record ID
            user_id: Optional user_id for user-scoped queries
            
        Returns:
            Record
            
        Raises:
            HTTPException: 404 if not found, 500 if query fails
        """
        record = await self.get(supabase, id, user_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.table_name.capitalize()} not found"
            )
        return record
    
    async def list(
        self, 
        supabase: Client,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List records with filtering and pagination.
        
        Args:
            supabase: Supabase client
            user_id: Optional user_id for user-scoped queries
            filters: Optional additional filters as {column: value}
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            ascending: Sort order (False = descending)
            
        Returns:
            List of records
            
        Raises:
            HTTPException: If query fails
        """
        try:
            query = supabase.table(self.table_name).select("*")
            
            # Add user_id filter if provided
            if user_id:
                query = query.eq("user_id", user_id)
            
            # Add additional filters
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            # Apply ordering and pagination
            query = query.order(order_by, desc=not ascending).range(offset, offset + limit - 1)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error listing {self.table_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list {self.table_name}"
            )
    
    async def update(
        self, 
        supabase: Client, 
        id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a record by ID.
        
        Args:
            supabase: Supabase client
            id: Record ID
            data: Updated data
            user_id: Optional user_id for user-scoped queries
            
        Returns:
            Updated record
            
        Raises:
            HTTPException: If update fails or record not found
        """
        try:
            # First check if record exists (and belongs to user if user_id provided)
            await self.get_or_404(supabase, id, user_id)
            
            query = supabase.table(self.table_name).update(data).eq("id", id)
            
            # Add user_id filter if provided
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating {self.table_name} {id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update {self.table_name}"
            )
    
    async def delete(
        self, 
        supabase: Client, 
        id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a record by ID.
        
        Args:
            supabase: Supabase client
            id: Record ID
            user_id: Optional user_id for user-scoped queries
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If deletion fails or record not found
        """
        try:
            # First check if record exists (and belongs to user if user_id provided)
            await self.get_or_404(supabase, id, user_id)
            
            query = supabase.table(self.table_name).delete().eq("id", id)
            
            # Add user_id filter if provided
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} {id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete {self.table_name}"
            )
