import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("socket Created succesfully")

soc.bind(("0.0.0.0", 12345))

print("socket binded!")

soc.listen(2)

print("listning")

client1, addr1 = soc.accept()

print("connected the first client")

client2, addr2 = soc.accept()

print("connected the second client")

while True:

    msg1 = client1.recv(1024)
    msg2 = client2.recv(1024)

    client2.send(msg1)
    client1.send(msg2)


    # client2.send(msg1)
    #
    # msg2 = client2.recv(1024)
    # # if not msg2:
    # #     break
    # client1.send(msg2)
    #
    #
    #
