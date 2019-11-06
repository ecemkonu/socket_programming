from socket import *

#A server application that receives messages from multi clients. 
import threading
import time
import random

class ThreadedServer():
    client_ips = []
    client_sockets = []
    falseGuesses = 0
    playerCount = 0 
    usernames = []
    registeredUsers = {}
    IpUsernamePairs = {}
    wordList = []
    game_state = []
    gameWaiting = True
    gameRunning = False
    gameEnded = False
    allRunsEnded = False
    addedUsers = 0
    
    def getGuessFromClient(self, client, word, wordGuesses, letterGuesses):

        stateChanged = False
        guess = client.recv(1024)
        guess = guess.decode('utf-8')
        guess = guess.lower() #lowercase every guess
        if word == guess:
            self.gameEnded = True
        else:
            if len(guess) > 1:
                self.falseGuesses+=1
                wordGuesses.append(guess)
            else:
                letterGuesses.append(guess)
                for i in range(len(word)):
                    if guess == word[i]:                
                        stateChanged = True
                        self.game_state[i] = guess
                if not stateChanged:
                    self.falseGuesses+= 1
                            
        if "".join(self.game_state) == word:
            self.gameEnded = True
            
        if self.falseGuesses == 7:
            self.gameEnded = True

        return guess
            


    def run_game(self, serverSocket):
        word = random.choice(self.wordList) #get a random word, users will try to find this
        for i in word:
            self.game_state.append('_')
        
        printStr = ""
        for i in self.game_state:
            printStr+= i
            printStr+= " "

        wordGuesses = []
        letterGuesses = []
        welcome_message= "Hangman game is starting\n"

        print(welcome_message) #server says that game is starting
        for socket in self.client_sockets: #for every client
            socket.send((welcome_message + "Word is\n"+ printStr +"\n").encode("utf-8")) #welcome to game, initial string is shown to let users know how many characters are in there

        while not self.gameEnded: #as long as game is not ended, word is not guessed or false guesses are wrong
            for socket in self.client_sockets: #iterate clients in order of joining game
                ip = self.client_ips[self.client_sockets.index(socket)]
                printStr = self.IpUsernamePairs[ip] + " will be playing next\n"
                for turn_info in self.client_sockets:
                    turn_info.send(printStr.encode('utf-8'))
                time.sleep(1)

                socket.send('Your turn\n'.encode('utf-8'))

                last_guess = self.getGuessFromClient(socket, word, wordGuesses, letterGuesses)
                game_state_update = "Letter guesses: " +' ,'.join(letterGuesses) + "\n"
                game_state_update +="Word Guesses: " + " ,".join(wordGuesses)+ "\n"
                print_string = ""
                for c in self.game_state:
                    print_string+= c+ " "
                for all_clients in self.client_sockets:
                    all_clients.send(game_state_update.encode("utf-8"))
                    all_clients.send(("Last guessed: " + last_guess + "\n").encode("utf-8"))
                    print_string = " ".join(self.game_state)
                    all_clients.send(("Word\n" +print_string+ "\n").encode("utf-8"))
        
        self.gameRunning = False
        if self.falseGuesses < 7:
            for all_clients in self.client_sockets:
                all_clients.send(("Game is won\n").encode('utf-8'))
                time.sleep(0.5)
  


    def listenToNewClient(self, client, addr):

        allowed = True
        username = client.recv(1024)
        username = username.decode('utf-8')
        print(username)
        time.sleep(1)
        password = client.recv(1024)
        password = password.decode('utf-8')
        print(password)
        if username in self.usernames:
            if password == self.registeredUsers[username]:
                self.client_ips.append(addr)
                self.client_sockets.append(client)
                self.IpUsernamePairs[addr] = username
            else:
                allowed = False
        else:
            self.usernames.append(username)
            self.registeredUsers[username] = password
            self.client_ips.append(addr)
            self.client_sockets.append(client)
            self.IpUsernamePairs[addr] = username
            with open("savedUsers.txt","a+") as myFile:
                myFile.write(username+ ' ' + password+'\n')
        if allowed:
            client.send("You joined the game\n".encode("utf-8"))
            self.addedUsers= self.addedUsers +1 
 
        if not allowed:
            client.close()
            exit(0)
        
        if self.addedUsers == self.playerCount:
            self.gameWaiting = False
            self.gameRunning = True


    def game_waiting(self, serverSocket):
        while self.gameWaiting:
            if self.playerCount == self.addedUsers:
                self.gameWaiting = False
                self.gameRunning = True
                break
            connectionSocket,addr=serverSocket.accept()
            if addr in self.client_ips:
                index = self.client_ips.index(addr)
                self.client_sockets[index].send("Wait for the game to start\n".encode('utf-8')) #if a recorded client tries to type, wait message is sent
            elif self.addedUsers < self.playerCount: #new users are added in listen to new client
                 self.listenToNewClient(connectionSocket, addr)
                    #wait for num of people to join
            else:
                print("Access to ", addr, "is unallowed, max num reached") #if there is not enough index space, do not allow!
                connectionSocket.close()
                    
    def game_running(self, serverSocket):
        while self.gameRunning:
            print('entered running game')
            self.run_game(serverSocket)
            self.allRunsEnded = False
                    #ask everyone when game finishes
                    #users can continue if they want to
                    #remove ones that do not want to
                    #finish if everyone specified that they do not want to continue
            removedList = []
            for client in self.client_sockets:
                client.send("Continue?: Y or N".encode('utf-8'))
                time.sleep(1) #time sleep is used to synchronize cpu with tcp
                continue_game = client.recv(1024).decode('utf-8')
                if continue_game == 'Y':
                    self.gameRunning = True
                else:
                    ind = self.client_sockets.index(client)
                    self.client_sockets[ind].close()
                    del self.client_ips[ind]
                    removedList.append(ind)   

            for ind in removedList:
                del self.client_sockets[ind] 
            if not self.gameRunning:
                self.allRunsEnded = True
            if self.allRunsEnded:
                break

    def __init__(self,serverPort, playerCount):

        self.playerCount = playerCount
        try:
            serverSocket=socket(AF_INET,SOCK_STREAM)


        except:
    
            print("Socket cannot be created!!!")
            exit(1)
            
        print("Socket is created...")

        with open("savedUsers.txt") as myFile: #user records
            for line in myFile:
                username, password = line.split()
                self.usernames.append(username)
                self.registeredUsers[username] = password

        with open("words.txt") as myFile:
            line = myFile.readline()
            wordlist = line.split()
            print(" ", len(wordlist), "words loaded")
            self.wordList = wordlist  #load words from a txt file

        try:
            serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        except:
    
            print ("Socket cannot be used!!!")
            exit(1)

        print ("Socket is being used...")

        try:
            serverSocket.bind(('',serverPort))
        except:
        
            print("Binding cannot de done!!!")
            exit(1)

        print ("Binding is done...")

        try:
            serverSocket.listen(45)
        except:
    
            print("Server cannot listen!!!")
            exit(1)

        print("The server is ready to receive")


        self.game_waiting(serverSocket)
        print(self.addedUsers)
        self.game_running(serverSocket)
        print("Game requests finished!!")
                    



if __name__=="__main__":
    serverPort=12000
    playerCount = int(input("How many players will be playing Hangman?\n"))

    ThreadedServer(serverPort, playerCount)
	
