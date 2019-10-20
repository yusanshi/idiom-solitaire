import json
from play import Player, MyGraph
import socketio
from multiprocessing import freeze_support
from config import TOKEN

me = Player('Me', 'smart')
idiom_data = open('idiom.json', encoding='utf-8').read()
idiom_data = json.loads(idiom_data)

graph = MyGraph(idiom_data)

cookie = "token=" + TOKEN

sio = socketio.Client()

round_count = 1
success_count = 0
wait_graph_to_update = 1

@sio.event
def connect():
    print('Connection established')


@sio.event
def disconnect():
    print('Disconnected from server')


@sio.event
def reply(data):
    global round_count
    global success_count
    global graph
    global wait_graph_to_update
    beginning = str(data)[:128]
    print('\nServer: ', beginning)
    if beginning.find('flag{') != -1:
        print('Found flag, exit!')
        sio.disconnect()
    elif len(data['data']) > 512:
        wait_graph_to_update = 1
        print('I lost.')
        round_count = 1
        success_count = 0
        graph = MyGraph(idiom_data)
        sio.disconnect()
    else:
        idiom = data['data'][:4]
        if idiom == '服务器给':
            pass
        elif idiom == '成功领取':
            wait_graph_to_update = 1
            round_count = 1
            success_count += 1
            print('Success count {}.'.format(success_count))
            graph = MyGraph(idiom_data)
        else:
            if wait_graph_to_update:
                sio.sleep(3)
            print('Round count {}'.format(round_count))
            print('Success count {}.'.format(success_count))
            round_count += 1
            current = idiom_data[idiom]['last']
            graph.remove_edge(idiom_data[idiom]['first'], current, key=idiom)
            target_pinyin, idiom = me.choose(graph, current)
            graph.remove_edge(current, target_pinyin, key=idiom)
            print('{}\t: {}'.format('Me', idiom))
            wait_graph_to_update = 0
            sio.emit('go', {'data': idiom})


@sio.event
def error(data):
    print('Error!', data)
    print(sio.sid)


if __name__ == "__main__":
    freeze_support()
    sio.connect('http://202.38.73.168:8081/',
                transports='websocket', headers={'Cookie': cookie})
    sio.wait()
