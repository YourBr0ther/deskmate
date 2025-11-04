#!/bin/bash

echo "🎯 Visual Movement Test - Watch the assistant move!"
echo "===================================================="
echo ""

# Get current position
echo "📍 Current Position:"
curl -s -X POST "http://localhost:8000/brain/analyze" \
  -H "Content-Type: application/json" \
  -d '{"include_room_state": true, "include_memory": false}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Assistant at: {d['context']['room']['assistant']['position']}\")"

echo ""
echo "🚶 Moving assistant in a pattern..."
echo ""

# Move in a square pattern
positions=("10,5" "10,10" "20,10" "20,5" "10,5")

for pos in "${positions[@]}"; do
    echo "➡️  Moving to position $pos..."
    curl -s -X POST "http://localhost:8000/brain/process" \
      -H "Content-Type: application/json" \
      -d "{
        \"message\": \"Move to position $pos\",
        \"persona_context\": {
          \"name\": \"Assistant\",
          \"personality\": \"Obedient\"
        }
      }" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"   Response: {d.get('response', 'No response')[:50]}...\")"

    sleep 2

    # Check new position
    curl -s -X POST "http://localhost:8000/brain/analyze" \
      -H "Content-Type: application/json" \
      -d '{"include_room_state": true, "include_memory": false}' | \
      python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"   Now at: {d['context']['room']['assistant']['position']}\")"
    echo ""
done

echo "✅ Movement test complete!"
echo "👁️  Check the frontend at http://localhost:3000 to see the assistant has moved!"