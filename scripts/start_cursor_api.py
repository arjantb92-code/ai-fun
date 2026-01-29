#!/usr/bin/env python3
"""
Cursor Agent HTTP API Server
Starts a local HTTP server on port 32123 that wraps cursor-agent CLI calls.

Usage:
    python scripts/start_cursor_api.py

The server exposes an OpenAI-compatible endpoint at:
    http://127.0.0.1:32123/v1/chat/completions
"""

import os
import sys
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

CURSOR_AGENT = "/Users/arjantebrake/.local/bin/cursor-agent"
CURSOR_API_KEY = os.getenv("CURSOR_API_KEY") or os.getenv("CUROS_API_KEY")  # Handle typo
PORT = 32123


class CursorAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        """Handle POST requests to /v1/chat/completions."""
        if self.path != "/v1/chat/completions":
            self.send_error(404, "Not Found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            # Extract prompt from messages
            messages = data.get("messages", [])
            if not messages:
                self.send_error(400, "No messages provided")
                return

            # Get the last user message
            prompt = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    prompt = msg.get("content", "")
                    break

            if not prompt:
                self.send_error(400, "No user message found")
                return

            # Call cursor-agent
            workspace = os.path.dirname(os.path.dirname(__file__))
            cmd = [
                CURSOR_AGENT,
                "--print",
                "--output-format", "text",
                "--workspace", workspace,
                "agent", prompt
            ]

            if CURSOR_API_KEY:
                cmd.extend(["--api-key", CURSOR_API_KEY])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=workspace
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                self.send_error(500, f"Cursor agent error: {error_msg}")
                return

            response_text = result.stdout.strip()

            # Format as OpenAI-compatible response
            response = {
                "id": "cursor-response",
                "object": "chat.completion",
                "created": 0,
                "model": data.get("model", "auto"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except subprocess.TimeoutExpired:
            self.send_error(504, "Request timeout")
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def log_message(self, format, *args):
        """Override to use stderr instead of stdout."""
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")


def main():
    if not os.path.exists(CURSOR_AGENT):
        print(f"❌ Cursor agent not found at: {CURSOR_AGENT}")
        print("   Install it first: npm install -g cursor-agent")
        sys.exit(1)

    # Test cursor-agent
    test_result = subprocess.run(
        [CURSOR_AGENT, "--version"],
        capture_output=True,
        text=True
    )
    if test_result.returncode != 0:
        print("❌ Cursor agent not working. Check installation.")
        sys.exit(1)

    server = HTTPServer(("127.0.0.1", PORT), CursorAPIHandler)
    print(f"🚀 Cursor Agent HTTP API Server")
    print(f"   Listening on: http://127.0.0.1:{PORT}/v1/chat/completions")
    if CURSOR_API_KEY:
        print(f"   ✓ API key loaded from .env")
    else:
        print(f"   ⚠️  No CURSOR_API_KEY in .env (using default auth)")
    print(f"\n   Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
