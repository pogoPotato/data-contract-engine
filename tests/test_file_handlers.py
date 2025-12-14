import pytest
from app.core.file_handlers import CSVHandler, JSONHandler, JSONLHandler, FileHandlerFactory


class TestCSVHandler:
    
    def test_read_chunks(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,Alice\n2,Bob\n3,Charlie")
        
        handler = CSVHandler()
        chunks = list(handler.read_chunks(str(csv_file), chunk_size=2))
        
        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert chunks[0][0]['name'] == 'Alice'
    
    def test_validate_format_valid(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,name\n1,Alice")
        
        handler = CSVHandler()
        assert handler.validate_format(str(csv_file)) == True
    
    def test_validate_format_invalid(self, tmp_path):
        csv_file = tmp_path / "test.txt"
        csv_file.write_text("not a csv")
        
        handler = CSVHandler()
        assert handler.validate_format(str(csv_file)) == False


class TestJSONHandler:
    
    def test_read_chunks_array(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('[{"id": 1}, {"id": 2}, {"id": 3}]')
        
        handler = JSONHandler()
        chunks = list(handler.read_chunks(str(json_file), chunk_size=2))
        
        assert len(chunks) == 2
        assert chunks[0][0]['id'] == 1
    
    def test_read_chunks_object_with_data(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"data": [{"id": 1}, {"id": 2}]}')
        
        handler = JSONHandler()
        chunks = list(handler.read_chunks(str(json_file), chunk_size=10))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 2


class TestJSONLHandler:
    
    def test_read_chunks(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}')
        
        handler = JSONLHandler()
        chunks = list(handler.read_chunks(str(jsonl_file), chunk_size=2))
        
        assert len(chunks) == 2
        assert chunks[0][0]['id'] == 1
    
    def test_skip_invalid_lines(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": 1}\ninvalid json\n{"id": 2}')
        
        handler = JSONLHandler()
        chunks = list(handler.read_chunks(str(jsonl_file), chunk_size=10))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 2


class TestFileHandlerFactory:
    
    def test_get_csv_handler(self):
        handler = FileHandlerFactory.get_handler('csv')
        assert isinstance(handler, CSVHandler)
    
    def test_get_json_handler(self):
        handler = FileHandlerFactory.get_handler('json')
        assert isinstance(handler, JSONHandler)
    
    def test_unsupported_type(self):
        with pytest.raises(ValueError):
            FileHandlerFactory.get_handler('xml')