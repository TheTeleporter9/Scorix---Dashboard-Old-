# Scorix Server Connection Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [MongoDB Connection Guide](#mongodb-connection-guide)
3. [Socket Server Connection Guide](#socket-server-connection-guide)
4. [Troubleshooting](#troubleshooting)
5. [Code Examples](#code-examples)
6. [Security Considerations](#security-considerations)

## Prerequisites

Before connecting to the Scorix services, ensure you have:

1. Required Python packages:
```bash
pip install pymongo socket-client-py threading json datetime
```

2. Network access to:
   - MongoDB Atlas cluster (port 27017)
   - Socket Server (default port 5001)

3. Valid credentials for MongoDB connection

## MongoDB Connection Guide

### Connection String Format
```
mongodb+srv://[username]:[password]@wro-scoring.n0khn.mongodb.net
```

### Authentication
1. Obtain credentials from system administrator
2. Store credentials securely (never in source code)
3. Use environment variables or configuration files

### Connection Example with Error Handling
```python
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os

class MongoDBConnection:
    def __init__(self):
        self.uri = os.getenv('MONGO_URI', 'mongodb+srv://[username]:[password]@wro-scoring.n0khn.mongodb.net')
        self.client = None
        self.db = None

    def connect(self):
        try:
            # Connect with timeout
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client['Wro-scoring']
            print("Successfully connected to MongoDB")
            return True
        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            return False
        except OperationFailure as e:
            print(f"Authentication failed: {e}")
            return False

    def get_collection(self, collection_name):
        if not self.db:
            self.connect()
        return self.db[collection_name]

    def close(self):
        if self.client:
            self.client.close()
```

### Available Collections
1. `gamescores` - Match scores and game data
   ```python
   {
       "Team1": {
           "Name": str,
           "Score": int,
           "Penalties": int
       },
       "Team2": {
           "Name": str,
           "Score": int,
           "Penalties": int
       },
       "timestamp": str,
       "match_id": str
   }
   ```

2. `competition_display` - Live display data
   ```python
   {
       "current_match": dict,
       "next_matches": list,
       "announcements": list,
       "last_update": str
   }
   ```

3. `live_announcement` - Real-time announcements
   ```python
   {
       "message": str,
       "priority": int,
       "timestamp": str,
       "duration": int
   }
   ```

## Socket Server Connection Guide

### Server Details
- Default Host: localhost (for local connections)
- Default Port: 5001
- Protocol: TCP
- Encoding: UTF-8
- Message Format: JSON

### Client Implementation Example
```python
import socket
import json
import threading
from typing import Callable, Dict, Any

class ScorixSocketClient:
    def __init__(self, host: str = 'localhost', port: int = 5001):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.callbacks: Dict[str, Callable] = {}
        self._listen_thread = None

    def connect(self) -> bool:
        """
        Establishes connection to the Scorix socket server
        Returns: bool indicating success
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Start listening thread
            self._listen_thread = threading.Thread(target=self._listen, daemon=True)
            self._listen_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """
        Register callback for specific event types
        """
        self.callbacks[event_type] = callback

    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Sends a message to the server
        Args:
            message: Dictionary to be sent as JSON
        Returns:
            bool indicating success
        """
        if not self.connected:
            return False

        try:
            json_msg = json.dumps(message)
            self.socket.send(json_msg.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            self.connected = False
            return False

    def _listen(self) -> None:
        """
        Background thread for listening to server messages
        """
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break

                message = json.loads(data.decode('utf-8'))
                event_type = message.get('type')
                
                if event_type in self.callbacks:
                    self.callbacks[event_type](message)
                    
            except Exception as e:
                print(f"Error in listener: {e}")
                self.connected = False
                break

    def close(self) -> None:
        """
        Closes the connection
        """
        self.connected = False
        if self.socket:
            self.socket.close()
```

### Usage Example
```python
def handle_score_update(message):
    print(f"Score Update: {message}")

def handle_announcement(message):
    print(f"Announcement: {message}")

# Create client instance
client = ScorixSocketClient()

# Register callbacks
client.register_callback('score_update', handle_score_update)
client.register_callback('announcement', handle_announcement)

# Connect to server
if client.connect():
    # Send a message
    client.send_message({
        "type": "score_update",
        "data": {
            "team1": "Team A",
            "score1": 100,
            "team2": "Team B",
            "score2": 95
        }
    })

# Don't forget to close when done
client.close()
```

## Troubleshooting

### MongoDB Connection Issues
1. Check network connectivity to MongoDB Atlas
2. Verify credentials are correct
3. Ensure IP address is whitelisted in MongoDB Atlas
4. Check for proper database/collection permissions

Common errors and solutions:
```python
try:
    # Your MongoDB operation
    pass
except pymongo.errors.ServerSelectionTimeoutError:
    print("Could not connect to MongoDB server. Check network/firewall.")
except pymongo.errors.OperationFailure as e:
    if e.code == 18:  # Authentication error
        print("Invalid credentials")
    elif e.code == 13:  # Authorization error
        print("Insufficient permissions")
```

### Socket Connection Issues
1. Verify server is running
2. Check if port 5001 is open
3. Ensure no firewall blocking
4. Verify correct host/IP address

Connection test script:
```python
def test_socket_connection(host='localhost', port=5001):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            print("Socket server is running")
            return True
        else:
            print(f"Connection failed with error code: {result}")
            return False
    except socket.error as e:
        print(f"Socket error: {e}")
        return False
    finally:
        sock.close()
```

## Security Considerations

1. **Never** hardcode credentials
2. Use environment variables:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   MONGO_URI = os.getenv('MONGO_URI')
   MONGO_USER = os.getenv('MONGO_USER')
   MONGO_PASS = os.getenv('MONGO_PASS')
   ```

3. Implement proper error handling
4. Use secure connections (TLS/SSL)
5. Implement timeouts
6. Close connections properly
7. Implement retry logic with backoff

Example .env file structure:
```
MONGO_URI=mongodb+srv://user:pass@wro-scoring.n0khn.mongodb.net
MONGO_USER=username
MONGO_PASS=password
SOCKET_HOST=localhost
SOCKET_PORT=5001
```

## Rate Limiting and Optimization

1. Implement connection pooling for MongoDB:
```python
from pymongo import MongoClient, ReadPreference

client = MongoClient(
    MONGO_URI,
    maxPoolSize=50,
    waitQueueTimeoutMS=2500,
    readPreference=ReadPreference.SECONDARY_PREFERRED
)
```

2. Implement reconnection logic:
```python
from retrying import retry

@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
def send_with_retry(client, data):
    try:
        client.send(data)
    except socket.error as e:
        print(f"Retry after error: {e}")
        raise  # Retry
```

Remember to properly handle cleanup in your application:
```python
import atexit

def cleanup():
    client.close()
    socket_client.close()

atexit.register(cleanup)
```
