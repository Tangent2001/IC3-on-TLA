---- MODULE LockServer ----

EXTENDS Apalache

\*
\* Simple lock server example.
\*
\* The system consists of a set of servers and a set of clients.
\* Each server maintains a single lock, which can be granted to a
\* client if it currently owns that lock.
\*

CONSTANT
	\* @type: Set(SERVER);
	Server,
	\* @type: Set(CLIENT);
	Client

VARIABLE
	\* @type: SERVER -> Bool;
	semaphore,
	\* @type: CLIENT -> Set(SERVER);
	clientlocks

vars == <<semaphore, clientlocks>>


\* Apalache处理时会将ConstInit转化为全大写，一定要注意
ConstInit ==
  /\ Server = {"S1_OF_SERVER","S2_OF_SERVER","S3_OF_SERVER"}
  /\ Client = {"C1_OF_CLIENT","C2_OF_CLIENT"}

\* A client c requests a lock from server s.
Connect(c, s) ==
    \* The server must currently hold the lock.
    /\ semaphore[s] = TRUE
    \* The client obtains the lock of s.
    /\ clientlocks' = [clientlocks EXCEPT ![c] = clientlocks[c] \cup {s}]
    /\ semaphore' = [semaphore EXCEPT ![s] = FALSE]


\* A client c relinquishes the lock of server s.
Disconnect(c, s) ==
    \* The client must currently be holding the lock of s.
    /\ s \in clientlocks[c]
    \* The relinquishes the lock of s.
    /\ clientlocks' = [clientlocks EXCEPT ![c] = clientlocks[c] \ {s}]
    /\ semaphore' = [semaphore EXCEPT ![s] = TRUE]

Init ==
    \* Initially each server holds its lock, and all clients hold
    \* no locks.
    /\ semaphore = [i \in Server |-> TRUE]
    /\ clientlocks = [i \in Client |-> {}]

Next ==
    \/ \E c \in Client, s \in Server : Connect(c, s)
    \/ \E c \in Client, s \in Server : Disconnect(c, s)

NextUnchanged == UNCHANGED vars

TypeOK ==
    /\ semaphore \in [Server -> BOOLEAN]
    /\ clientlocks \in [Client -> SUBSET Server]

\* Two different clients cannot hold the lock of the same server simultaneously.
Inv == \A ci,cj \in Client : (clientlocks[ci] \cap clientlocks[cj] # {}) => (ci = cj)

T1 ==
    \A s \in Server : \E c1,c2 \in Client:
	  /\  \/ semaphore[s] = FALSE
	      \/ s \notin clientlocks[c2]
          /\ s \notin clientlocks[c1]
P ==
     /\ TypeOK
     /\ Inv
F1 ==
     /\ TypeOK
     /\ Inv
     /\ T1

====

