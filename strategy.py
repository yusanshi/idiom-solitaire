def kill(level, x, graph):
    '''
    return True if x ∈ Kn (level means n)
    for example,
    if kill(0, x, graph) == True, then add x to K0
    '''
    if level == 0:
        return graph.out_degree(x) == 0
    else:
        for p in graph.successors(x):
            # remove an edge from x to p
            idiom_1 = list(graph.adj[x][p])[0]
            graph.remove_edge(x, p, key=idiom_1)
            exist = False
            for q in graph.successors(p):
                # remove an edge from p to q
                idiom_2 = list(graph.adj[p][q])[0]
                graph.remove_edge(p, q, key=idiom_2)
                temp = kill(level -1, q, graph)
                # add the removed edge
                graph.add_edge(p, q, key=idiom_2)
                if temp:
                    exist = True
                    break
            # add the removed edge
            graph.add_edge(x, p, key=idiom_1)
            if exist == False:
                return False
        return True


def safe(level, x, graph):
    '''
    return True if x ∈ Sn (level means n)
    for example,
    if safe(0, x, graph) == True, then add x to S0
    '''
    if level == 0:
        for p in graph.successors(x):
            if graph.out_degree(p) == 0:
                return False
        return True
    else:
        for p in graph.successors(x):
            # remove an edge from x to p
            idiom_1 = list(graph.adj[x][p])[0]
            graph.remove_edge(x, p, key=idiom_1)
            exist = False
            for q in graph.successors(p):
                # remove an edge from p to q
                idiom_2 = list(graph.adj[p][q])[0]
                graph.remove_edge(p, q, key=idiom_2)
                temp = safe(level -1, q, graph)
                # add the removed edge
                graph.add_edge(p, q, key=idiom_2)
                if temp:
                    exist = True
                    break
            # add the removed edge
            graph.add_edge(x, p, key=idiom_1)
            if exist == False:
                return False
        return True


def kill_worker(level, current, graph, calc_set_divided, one_only=False):
    '''
    worker for multiprocessing
    '''
    result = []
    for x in calc_set_divided:
        idiom_temp = list(graph.adj[current][x])[0]
        graph.remove_edge(current, x, key=idiom_temp)
        if kill(level, x, graph):
            result.append(x)
        graph.add_edge(current, x, key=idiom_temp)
        if one_only and len(result) != 0:
            break
    return result


def safe_worker(level, current, graph, calc_set_divided, one_only=False):
    '''
    worker for multiprocessing
    '''
    result = []
    for x in calc_set_divided:
        idiom_temp = list(graph.adj[current][x])[0]
        graph.remove_edge(current, x, key=idiom_temp)
        if safe(level, x, graph):
            result.append(x)
        graph.add_edge(current, x, key=idiom_temp)
        if one_only and len(result) != 0:
            break
    return result
