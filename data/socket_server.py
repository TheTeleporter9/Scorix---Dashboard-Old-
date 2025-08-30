"""
TCP Socket Server for Scorix Dashboard
"""

import socket
import threading
import json
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import messagebox

class ScorexSocketServer:
    def __init__(self, host: str = '', port: int = 5001):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.clients = []
        self.root: Optional[tk.Tk] = None

    def start_server(self, root: tk.Tk) -> None:
        """Start the TCP server in a background thread"""
        self.root = root
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # Try to bind to the port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            
            # Start listening in a background thread
            server_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
            server_thread.start()
            
            if self.host == '':
                # Get the actual IP address
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                messagebox.showinfo("Server Started", f"Server is running on:\nIP: {local_ip}\nPort: {self.port}")
            else:
                messagebox.showinfo("Server Started", f"Server is running on:\nIP: {self.host}\nPort: {self.port}")
                
        except Exception as e:
            messagebox.showerror("Server Error", f"Could not start server: {str(e)}")
            self.stop_server()

    def stop_server(self) -> None:
        """Stop the TCP server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients = []

    def _listen_for_connections(self) -> None:
        """Listen for incoming connections"""
        while self.is_running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                self.clients.append(client_socket)
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            except:
                if self.is_running:  # Only show error if we didn't stop intentionally
                    messagebox.showerror("Connection Error", "Error accepting client connection")

    def _handle_client(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle communication with a connected client"""
        try:
            while self.is_running:
                # Receive data from the client
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    # Try to parse as JSON
                    message = json.loads(data.decode())
                    # Process the message and send response
                    response = self._process_message(message)
                    client_socket.send(json.dumps(response).encode())
                except json.JSONDecodeError:
                    # If not JSON, treat as text
                    response = self._process_text_message(data.decode())
                    client_socket.send(response.encode())

        except Exception as e:
            if self.is_running:  # Only show error if we didn't stop intentionally
                print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)

    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON message from a client"""
        # TODO: Implement message processing logic
        return {"status": "received", "message": message}

    def _process_text_message(self, message: str) -> str:
        """Process a text message from a client"""
        # TODO: Implement text message processing logic
        return f"Received: {message}"

    def broadcast(self, message: str) -> None:
        """Send a message to all connected clients"""
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                if client in self.clients:
                    self.clients.remove(client)

    def get_server_info(self) -> Dict[str, Any]:
        """Get information about the server status"""
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return {
            "running": self.is_running,
            "host": self.host or local_ip,
            "port": self.port,
            "clients": len(self.clients)
        }