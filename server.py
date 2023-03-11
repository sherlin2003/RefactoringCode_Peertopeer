import socket
import uuid
#generating 4-bytes random ids
import pickle

import threading
#creating multiple threads
import sys

port=9300
max_chunk=1024

class excepclass(Exception):
    print("Thread didnt Start")

class server:
    def __init__(self,port,no_of_connections):
        self.port=port
        self.host=socket.gethostbyname(socket.gethostname()) 
        self.no_of_connections=no_of_connections
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.file={}#list of files registered
        self.peers={}#list of peers connected

        x=True
        while x:
            try:
                self.sock.bind((self.host,self.port))
            except OverflowError:
                self.port=input("Enter new port(>3000)")#alternative portno
            else:
                x=False

        print("listening through [",self.host,":",self.port,"]")



    def peer_threads(self, client, addr):
        peer_id = uuid.uuid4().int >> 115
        self.peers[peer_id] = addr
        client.send(pickle.dumps((peer_id, addr[1])))
        
        while True:
            method = pickle.loads(client.recv(max_chunk))
            print("Method opted by peer_id-", peer_id, " is ", method)
        
            if method == "search":
                self.handle_search(client)
            elif method == 'register':
                self.handle_register(client, peer_id)
            elif method == 'bye':
                self.handle_bye(client, peer_id)
                break

    def handle_search(self, client):
        client.send(pickle.dumps("ok"))
        file_name = pickle.loads(client.recv(max_chunk))
        
        if file_name in self.file:
            client.send(pickle.dumps('found'))
            reply = pickle.loads(client.recv(max_chunk))
        
            if reply == 'send':
                content = pickle.dumps(self.file[file_name])
                client.send(content)
                peerno = pickle.loads(client.recv(max_chunk))
                client.send(pickle.dumps(self.peers[peerno]))
            else:
                print("only search is done..")
        else:
            client.send(pickle.dumps("not found"))
    
    def handle_register(self, client, peer_id):
        client.send(pickle.dumps('ok'))
        file_name = pickle.loads(client.recv(max_chunk))
        print("For registering file by peer_id-", peer_id)
        
        if file_name in self.file:
            self.file[file_name].append(peer_id)
        else:
            self.file[file_name] = [peer_id]
        
        client.send(pickle.dumps('success'))
    
    def handle_bye(self, client, peer_id):
        client.send(pickle.dumps('ok'))
        
        list1 = []
        for i in self.file:
            try:
                self.file[i].remove(peer_id)
                if not self.file[i]:
                    list1.append(i)
            except ValueError:
                continue
        
        for i in list1:
            del self.file[i]
        
        del self.peers[peer_id]
    
        

    def connections(self):
        self.sock.listen(self.no_of_connections)
        
        while True:
            client,addr=self.sock.accept()   #accepting connections
            print("Connected with ",addr)


            #thread creation for each peer
            try:
                t=threading.Thread(target=self.peer_threads,args=(client,addr))
                #creating threads and passing arguments
                t.start()
                #starting the thread
                print("thread started")

            except excepclass as e:
                print("Error Occurred" + str(e))

        self.sock.close()


if __name__=='__main__':
    s=server(port,5)
    s.connections()
    