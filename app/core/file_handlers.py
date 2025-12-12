from abc import ABC, abstractmethod
from typing import Iterator, List, Dict, Any
import json
import pandas as pd
import math
import logging


class FileHandler(ABC):
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def read_chunks(self, file_path: str, chunk_size: int) -> Iterator[List[Dict[str, Any]]]:
        pass
    
    @abstractmethod
    def validate_format(self, file_path: str) -> bool:
        pass


class CSVHandler(FileHandler):
    
    def read_chunks(self, file_path: str, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        try:
            for chunk in pd.read_csv(
                file_path,
                chunksize=chunk_size,
                encoding='utf-8',
                skipinitialspace=True,
                skip_blank_lines=True,
                on_bad_lines='warn'
            ):
                chunk.columns = chunk.columns.str.strip()
                records = chunk.to_dict('records')
                records = self._clean_records(records)
                yield records
                
        except UnicodeDecodeError:
            for chunk in pd.read_csv(
                file_path,
                chunksize=chunk_size,
                encoding='latin1',
                skipinitialspace=True
            ):
                chunk.columns = chunk.columns.str.strip()
                records = chunk.to_dict('records')
                records = self._clean_records(records)
                yield records
    
    def _clean_records(self, records: List[Dict]) -> List[Dict]:
        cleaned = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if isinstance(value, float) and math.isnan(value):
                    cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            cleaned.append(cleaned_record)
        return cleaned
    
    def validate_format(self, file_path: str) -> bool:
        try:
            pd.read_csv(file_path, nrows=5)
            return True
        except Exception:
            return False


class JSONHandler(FileHandler):
    
    def read_chunks(self, file_path: str, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            if 'data' in data:
                data = data['data']
            else:
                data = [data]
        elif not isinstance(data, list):
            raise ValueError("JSON must be object or array")
        
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
    
    def validate_format(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except json.JSONDecodeError:
            return False


class JSONLHandler(FileHandler):
    
    def read_chunks(self, file_path: str, chunk_size: int = 1000) -> Iterator[List[Dict[str, Any]]]:
        chunk = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    chunk.append(record)
                    
                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []
                        
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Skipping invalid line: {e}")
                    continue
        
        if chunk:
            yield chunk
    
    def validate_format(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    if line.strip():
                        json.loads(line)
            return True
        except json.JSONDecodeError:
            return False


class FileHandlerFactory:
    
    @staticmethod
    def get_handler(file_type: str) -> FileHandler:
        handlers = {
            'csv': CSVHandler(),
            'json': JSONHandler(),
            'jsonl': JSONLHandler(),
        }
        
        handler = handlers.get(file_type.lower())
        if not handler:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return handler