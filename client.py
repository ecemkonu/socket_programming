from socket import *
import time

serverName="localhost"
serverPort=12000

clientSocket=socket(AF_INET,SOCK_STREAM)

username = input('User name:')
password = input('Password:')

print(username)
print(password)
clientSocket.connect((serverName,serverPort))

clientSocket.send(username.encode('utf-8'))

time.sleep(1)

clientSocket.send(password.encode('utf-8'))

while True:

    recieved = clientSocket.recv(1024)
    recieved = recieved.decode('utf-8')
    print(recieved)
    if recieved == 'Your turn\n':
        message=input('Enter your guess: ')
        time.sleep(0.5)
        clientSocket.send(message.encode('utf-8'))

    elif recieved == "Continue?: Y or N":
        message = input("\nEnter your response here: ")
        time.sleep(0.5)
        clientSocket.send(message.encode('utf-8'))
