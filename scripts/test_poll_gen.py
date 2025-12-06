
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json

# パスを通す
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.poll_manager import create_poll_draft_from_analysis

class TestPollGeneration(unittest.TestCase):
    @patch('features.poll_manager.get_ollama_client')
    @patch('features.poll_manager.create_poll')
    def test_create_poll_draft(self, mock_create_poll, mock_get_client):
        # Mock Ollama response
        mock_client = MagicMock()
        mock_client.generate_poll_draft.return_value = {
            "question": "公園の遊具について",
            "options": ["新しい遊具が欲しい", "修理してほしい", "現状で満足", "その他"],
            "description": "市民の声から作成"
        }
        mock_get_client.return_value = mock_client
        
        # Mock create_poll return
        mock_create_poll.return_value = 123
        
        # Test execution
        summary = "公園の遊具が古くて危険という意見が多い"
        poll_id = create_poll_draft_from_analysis(summary)
        
        # Assertions
        self.assertEqual(poll_id, 123)
        mock_client.generate_poll_draft.assert_called_once_with(summary)
        mock_create_poll.assert_called_once_with(
            question="公園の遊具について",
            choices=["新しい遊具が欲しい", "修理してほしい", "現状で満足", "その他"],
            description="市民の声から作成"
        )
        print("Test passed!")

if __name__ == '__main__':
    unittest.main()
