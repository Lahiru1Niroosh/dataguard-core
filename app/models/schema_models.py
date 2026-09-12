from typing import List, Optional
from pydantic import BaseModel


class ColumnInfo(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool


class TableInfo(BaseModel):
    table_name: str
    columns: List[ColumnInfo]


class SchemaSnapshot(BaseModel):
    schema_name: str
    tables: List[TableInfo]