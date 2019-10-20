import json
import networkx as nx
import random
import matplotlib.pyplot as plt
from strategy import kill, kill_worker, safe, safe_worker
from multiprocessing import freeze_support
from parallel import multiprocess_calc
from config import CAPACITY


class MyGraph(nx.MultiDiGraph):
    def __init__(self, data):
        '''
        initiate a digraph based on idiom dict
        where each node is a pinyin string
        '''
        super().__init__()
        for idiom in data:
            self.add_edge(data[idiom]['first'],
                          data[idiom]['last'],
                          key=idiom)

    def get_outing_edge(self, node):
        '''
        node is a pinyin string
        return all outing edges
        example: if node is 'di',
        then return {'yi':['低回不已'], 'yan':['低眉顺眼'], ...}
        '''
        result = {}
        for x in self.successors(node):
            result[x] = list(self.adj[node][x])
        return result

    def show_graph(self):
        # don’t use this, will stuck as the nodes and edges are too many
        nx.draw(self, with_labels=True)
        plt.show()


class Player():
    def __init__(self, name, mode):
        self.name = name
        assert mode in ['manual', 'random',
                        'smart'], "mode must be 'manual', 'random' or 'smart'"
        self.mode = mode  # 'manual', 'random', 'smart'

    def emit(self, current, graph):
        '''
        give a new pinyin string according to graph and 'current' pinyin
        then make the edge in graph unavaiable (remove the edge)
        '''
        target_pinyin, idiom = self.choose(graph, current)
        graph.remove_edge(current, target_pinyin, key=idiom)
        print('{}\t: {}'.format(self.name, idiom))
        return target_pinyin

    def choose(self, graph, current):
        outing_edge = graph.get_outing_edge(current)
        assert len(outing_edge) > 0, 'No available choice for {}'.format(current)

        if self.mode == 'manual':
            all_idioms = outing_edge.values()
            all_idioms = [item for sublist in all_idioms for item in sublist]
            print('Current available choice: ', all_idioms)
            while True:
                choice = input('Input your choice (idiom): ')
                if choice not in all_idioms:
                    print('Your choice {} is not in {}'.format(
                        choice, list(all_idioms)))
                else:
                    break
            for x in list(outing_edge):
                if choice in outing_edge[x]:
                    target_pinyin = x
                    break
            return target_pinyin, choice
        elif self.mode == 'random':
            target_pinyin = random.choice(list(outing_edge))
            idiom = outing_edge[target_pinyin][0]
            return target_pinyin, idiom
        elif self.mode == 'smart':
            all_list = list(outing_edge)
            s0_list = []
            s1_list = []
            s2_list = []
            k0_list = []
            k1_list = []
            k2_list = []

            if CAPACITY[0]:
                for x in all_list:
                    idiom_temp = list(graph.adj[current][x])[0]
                    graph.remove_edge(current, x, key=idiom_temp)
                    if kill(0, x, graph):
                        k0_list.append(x)
                    graph.add_edge(current, x, key=idiom_temp)
                print('k0', k0_list)

            if CAPACITY[1]:
                for x in all_list:
                    idiom_temp = list(graph.adj[current][x])[0]
                    graph.remove_edge(current, x, key=idiom_temp)
                    if safe(0, x, graph):
                        s0_list.append(x)
                    graph.add_edge(current, x, key=idiom_temp)
                print('s0', s0_list)

            if CAPACITY[2]:
                for x in all_list:
                    idiom_temp = list(graph.adj[current][x])[0]
                    graph.remove_edge(current, x, key=idiom_temp)
                    if kill(1, x, graph):
                        k1_list.append(x)
                    graph.add_edge(current, x, key=idiom_temp)
                print('k1', k1_list)

            # k0, s0, k1 do not use multiprocessing
            # while s1, k2, s2 use it

            # TODO
            # BUG in multiprocessing
            # May possibly cause wrong result when calculating Kn and Sn list using multiprocessing.
            # Since graph is shared between all process, modification made by one process may influence
            # other processes.
            #
            # In additin, in function multiprocess_calc(), terminating other processes when one of them
            # already get a desirable result may contribute to a circumstance where a process has
            # remove an edge but was killed before adding such edge.
            # I realized this when my result of s2_list is incorrect
            # (my s2_list is not null but I lost the game just the next round)
            # Since this bug occurs rarely and I'm busy on my homework I just leave it as it is.
            #
            # How to solve? Passing the copy of graph instead of graph's inference?
            # (I think passing graph to a function is to pass it's inference which could
            # cause a changed graph, maybe I'm wrong.)

            if CAPACITY[3]:
                s1_list += multiprocess_calc(current,
                                             graph, s0_list, safe_worker, 1)
                print('s1', s1_list)

            if CAPACITY[4]:
                k2_list += multiprocess_calc(current,
                                             graph, all_list, kill_worker, 2, one_only=True)
                print('k2', k2_list)

            if CAPACITY[5]:
                s2_list += multiprocess_calc(current,
                                             graph, s1_list, safe_worker, 2, one_only=True)
                print('s2', s2_list)

            k1_list_real = [x for x in s0_list if x in k1_list]
            k2_list_real = [x for x in s1_list if x in k2_list]
            print('k0_list', k0_list)
            print('k1_list_real', k1_list_real)
            print('k2_list_real', k2_list_real)
            final_list = k0_list + k1_list_real + k2_list_real + \
                s2_list + s1_list + s0_list + all_list
            target_pinyin = final_list[0]
            idiom = outing_edge[target_pinyin][0]
            return target_pinyin, idiom


class Game():
    def __init__(self, idiom_data, initial_idiom, player_one, player_two):
        '''
        Example parameter:
        idiom_data:
            {
                "阿鼻地狱": {
                    "first": "a",
                    "last": "yu"
                },
                "阿党比周": {
                    "first": "e",
                    "last": "zhou"
                },
                ......
            }
        initial_idiom: '阿鼻地狱'
        players: ['Me', 'Robot']
        '''
        self.graph = MyGraph(idiom_data)
        assert initial_idiom in idiom_data, '{} is not in idiom dataset.'.format(
            initial_idiom)
        self.current = idiom_data[initial_idiom]['last']
        self.graph.remove_edge(
            idiom_data[initial_idiom]['first'], self.current, key=initial_idiom)
        self.players = (Player(*player_one), Player(*player_two))

    def run(self):
        count = 1
        game_over = False
        while True:
            print('Round {}'.format(count))
            count += 1
            # Omit in turn
            for player in self.players:
                try:
                    self.current = player.emit(self.current, self.graph)
                except Exception as e:
                    print(e)
                    print('{} Lost!'.format(player.name))
                    game_over = True
                    break
            print()
            if game_over:
                break


def play(player_one, player_two):
    idiom_data = open('idiom.json', encoding='utf-8').read()
    idiom_data = json.loads(idiom_data)
    game = Game(idiom_data, input('Initial idiom: '), player_one, player_two)
    game.run()


if __name__ == "__main__":
    freeze_support()
    play(('Me', 'smart'), ('Robot', 'random'))
