import client

if __name__ == '__main__':
    try:
        client.launchStreamClient()
    except KeyboardInterrupt:
        print('\nGoodbye!')