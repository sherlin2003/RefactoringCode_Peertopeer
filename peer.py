import socket
import sys
import threading
import pickle
import traceback
import re
import queue

max_chunk=1024


class excepclass(Exception):
    print("Thread didnt Start")
    
class excepclass1(Exception):
    print("File Transfer Failed")
    



class peer:
    def __init__(self,host,port,no_of_connections):
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host#ip address of the server192.168.29.27
        self.port=port#portno of the server
        print("\n")
        print(self.host,":",self.port)
        self.no_of_connections=no_of_connections#maximum no.of.connections

        try:
            self.s.connect((self.host,self.port))
            #trying for connection with the server
        except(ConnectionRefusedError):
            print("Failed to establish connetion with server\n")
            sys.exit()
        except(TimeoutError):
            print('\npeer not responding connection failed\n')
            sys.exit()
        else:
            #receiving peer_id and port of the peer
            a=self.s.recv(max_chunk)
            a=pickle.loads(a)
            print("\nConnection Established:\nPeer_ID:",a[0])
            self.peerport=a[1]#port available for this peer machine



    def download(self,addr,file_name):
        try:
            #downloading the file
            #creating a client mode
            self.s1=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.s1.connect(addr)
            self.s1.send(pickle.dumps(file_name))
            a=pickle.loads(self.s1.recv(max_chunk))
            var=False
            if(a=='filefound'):
                print("filefound")
                self.s1.send(pickle.dumps('send'))
                #opening the output file
                file_input=open(file_name,'wb')
                txt='sent'
                data=self.s1.recv(max_chunk)
                #writing into the file
                while True:
                    file_input.write(data)
                    data=self.s1.recv(max_chunk)
                    a=re.findall(txt,str(data))
                    if(a):
                        break
                file_input.close()
                self.s1.send(pickle.dumps('received'))
                var=True
            elif(a=='filenotfound'):
                var=False
                self.s1.close()
        except(ConnectionRefusedError):
            print("\nConnection not able to establish with server\n")
            var=False
        except(TimeoutError):
            print("\npeer not responding connection failed")
            var=False
        return var


    def sendfile(self,client,addr,que):
        try:
            print("Preparing for sending to peer")
            #sending the file from the peer
            #containing it
            file_name=client.recv(max_chunk)
            file_name=pickle.loads(file_name)
            f=open(file_name,'rb')
            msg='filefound'
            client.send(pickle.dumps(msg))
            acknowledge=pickle.loads(client.recv(max_chunk))
            if(acknowledge=='send'):
                #reading the file
                #reading max_chunk from file
                a=f.read(max_chunk)
                while(a):
                    client.send(a)
                    a=f.read(max_chunk)
                f.close()
                client.send(pickle.dumps('sent'))
                data=pickle.loads(client.recv(max_chunk))
                #if reply is received file is sent
                if(data=='received'):
                    print(file_name+' sent')
                    client.close()
        except(FileNotFoundError):
            a="Filenotfound"
            client.send(pickle.dumps(a))
            que.put(False)
            
        except excepclass1 as e:
            print("Error Occurred" + str(e))
            que.put(False)
        
        else:
            que.put('okay')

    def search(self, file_name):
        self.s.send(pickle.dumps('search'))
    
        reply = pickle.loads(self.s.recv(max_chunk))
        if reply != 'ok':
            return False
    
        self.s.send(pickle.dumps(file_name))
    
        data = pickle.loads(self.s.recv(max_chunk))
        if data == 'not found':
            print("File not found with any peer")
            return False
        if data != 'found':
            return False
    
        proceed = input("\nFile Found\nProceed further to download(y/n)\n")
        if proceed != 'y':
            self.s.send(pickle.dumps('n'))
            return 'sch'
    
        self.s.send(pickle.dumps('send'))
    
        data = pickle.loads(self.s.recv(max_chunk))
        if not data:
            return False
    
        if len(data) == 1:
            peer = data[0]
        else:
            print("Select the peer from which the file can be extracted")
            for i, peer in enumerate(data):
                print(i+1, "->", peer)
            choice = int(input("Enter the choice of the peer: "))
            peer = data[choice-1]
    
        self.s.send(pickle.dumps(peer))
    
        addr = pickle.loads(self.s.recv(max_chunk))
        return self.download(addr, file_name)

    def seed(self):
        try:
            #making the peer for seeding
            self.s1=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.host1=socket.gethostbyname(socket.gethostname())#host of the peer
            self.s1.bind((self.host,self.peerport))
            self.s1.listen(self.no_of_connections)

            while True:
                #accepting clients
                client,addr=self.s1.accept()
                print("Connected with "+str(addr[0]),":",addr[1])

                try:
                    que=queue.Queue()
                    #creating of threads for peers individually
                    t=threading.Thread(target=self.sendfile,args=(client,addr,que))
                    t.start()
                    var=que.get()
                    self.s1.close()
                    return var
                
                except excepclass as e:
                    print("Error Occurred" + str(e))
                    #tracing back to normal state without halting
                    traceback.print_exc()
                    
                
        except(KeyboardInterrupt):
            print("seeding stopped")
        return True


    def register(self,file_name):
        #for registering the file
        self.s.send(pickle.dumps('register'))
        reply=pickle.loads(self.s.recv(max_chunk))
        #asking for reply
        if(reply=='ok'):
            self.s.send(pickle.dumps(file_name))
            reply=pickle.loads(self.s.recv(max_chunk))
            if(reply=='success'):
                #asking for seeding 
                #conformation is acknowledged
                proceed=input("\nFile registered.\nproceed to seed(y/n)\n")
                if(proceed=='y'):
                    print("seeding mode\n")
                    var=self.seed()
                    return var
                else:
                    return True
            else:
                return False
        else:
            return False


    def quit(self):
        self.s.send(pickle.dumps('bye'))
        if(pickle.loads(self.s.recv(max_chunk))=='ok'):
            self.s.close()
            sys.exit(0)


#Entering the ip address and portno of the server
ip_address=input("\n\nEnter the ip address of the server\n")
port_no=int(input("Enter the portno of the server\n"))

p=peer(ip_address,port_no,5)


while True:
    #methods which can be done
    #select any one of the below
    print("\n\n1.Register and Seed\n")
    print("2.Search and Download\n")
    print("3.Quit\n")

    choice=int(input("\n\nEnter your choice(1/2/3):\n"))
    if(choice==1):
        #for registering the file
        file_name=input("\nEnter the filename to register:\n")
        try:
            #try opening the file
            file=open(file_name,'r')
        except(FileNotFoundError):
            print("File not found in this directory\n")
        else:
            file.close()
        a=p.register(file_name)
        #result of registering the file to the centralized directory
        if(a=='okay'):
            print("Registration and seeding successful")
        else:
            if(a):
                print("Registration successful but seeding falied")
            else:
                print("Registration and seeding failed")
    elif(choice==2):
        file_name=input("Enter the filename to search:\n")
        b=p.search(file_name)
        if(b=='sch'):
            print("Only search successful")
        else:
            if(b):
                print("search and download successful")
            else:
                print("search and download failed")
    elif(choice==3):
        p.quit()






