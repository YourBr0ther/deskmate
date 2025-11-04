#!/bin/bash

echo "========================================="
echo "PHASE 7: Brain Council System Test Suite"
echo "========================================="
echo ""

# Test 1: Basic Brain Council Test
echo "Test 1: Basic Brain Council Functionality"
echo "-----------------------------------------"
curl -s -X GET "http://localhost:8000/brain/test" | python3 -m json.tool
echo ""

# Test 2: Process Message with Movement Request
echo "Test 2: Movement Action Generation"
echo "----------------------------------"
curl -s -X POST "http://localhost:8000/brain/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please move to position 30, 8",
    "persona_context": {
      "name": "Assistant",
      "personality": "Helpful and attentive"
    }
  }' | python3 -m json.tool
echo ""

# Test 3: Process Message with Object Interaction
echo "Test 3: Object Interaction Request"
echo "----------------------------------"
curl -s -X POST "http://localhost:8000/brain/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you turn on the lamp?",
    "persona_context": {
      "name": "Assistant",
      "personality": "Efficient and task-oriented"
    }
  }' | python3 -m json.tool
echo ""

# Test 4: Context Analysis (Memory & Room State)
echo "Test 4: Context Analysis"
echo "------------------------"
curl -s -X POST "http://localhost:8000/brain/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "include_room_state": true,
    "include_memory": true,
    "persona_name": "Assistant"
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); print('Room Objects:', len(data['context']['room']['room']['objects'])); print('Memory Messages:', data['context']['memory']['message_count']); print('Assistant Position:', data['context']['room']['assistant']['position'])"
echo ""

# Test 5: Conversation Memory Integration
echo "Test 5: Memory Context Test"
echo "---------------------------"
# Add a message to memory
curl -s -X POST "http://localhost:8000/brain/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is John and I like blue colors",
    "persona_context": {
      "name": "Assistant",
      "personality": "Friendly"
    }
  }' > /dev/null

# Test if it remembers
curl -s -X POST "http://localhost:8000/brain/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my name and what color do I like?",
    "persona_context": {
      "name": "Assistant",
      "personality": "Friendly"
    }
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); print('Response:', data.get('response', 'No response')[:100] + '...')"
echo ""

# Test 6: Complex Action Sequence
echo "Test 6: Complex Action Sequence"
echo "-------------------------------"
curl -s -X POST "http://localhost:8000/brain/process" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Walk to the desk, then go to the window",
    "persona_context": {
      "name": "Assistant",
      "personality": "Methodical"
    }
  }' | python3 -c "import sys, json; data = json.load(sys.stdin); print('Actions generated:', len(data.get('actions', [])), 'actions'); [print(f\"  - {a['type']}: {a.get('target', 'N/A')}\") for a in data.get('actions', [])]"
echo ""

echo "========================================="
echo "Phase 7 Test Complete!"
echo "========================================="
echo ""
echo "✅ Check for:"
echo "  - Council reasoning in responses"
echo "  - Generated actions matching requests"
echo "  - Memory context being used"
echo "  - Proper mood/emotional states"
echo "  - Room awareness in responses"