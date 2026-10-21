#!/usr/bin/env python3
# slitherlink.py: Template para implementação do projeto de Inteligência Artificial 2025/2026.
# Devem alterar as classes e funções neste ficheiro de acordo com as instruções do enunciado.
# Além das funções e classes sugeridas, podem acrescentar outras que considerem pertinentes.

# Grupo 03:
# 114791 Felipe Sant'Ana
# 114613 João Tamagnini

import random, copy
from sys import stdin
from collections import defaultdict

import utils
from utils import *

from search import (
    Problem,
    Node,
    astar_search,
    breadth_first_tree_search,
    depth_first_tree_search,
    greedy_search,
    recursive_best_first_search,
)


class SlitherlinkState:
    state_id = 0

    def __init__(self, board, active_edges=None, inactive_edges=None, is_valid=True):
        self.board = board
        self.active_edges = active_edges if active_edges is not None else set()
        self.inactive_edges = inactive_edges if inactive_edges is not None else set()
        self.is_valid = is_valid
        self.id = SlitherlinkState.state_id
        SlitherlinkState.state_id += 1
    
    def __lt__(self, other):
        return self.id < other.id


class Board:
    """Representação interna de um tabuleiro de Slitherlink."""
    
    def __init__(self, lines):
        self._cell_values = lines
        self._rows = len(lines)
        self._cols = len(lines[0])
        self._edges = set()
        
    def get_cells_adjacent_to_edge(self, edge) -> list:
        """Devolve uma lista das células que fazem
        fronteira com a aresta enviada no argumento"""
        type, row, col = edge
        cells = []
        if type == 'h':
            if row < self._rows:
                cells.append((row, col))
            if row > 0:
                cells.append((row - 1, col))
        else:
            if col < self._cols:
                cells.append((row, col))
            if col > 0:
                cells.append((row, col - 1))
        return cells

    def adjacent_cell(self, cell:tuple) -> list:
        """Devolve uma lista das células que fazem
        fronteira com a célula enviada no argumento"""
        row, column = cell
        adjacent_cells = []
        if row > 0:
            adjacent_cells.append((row-1, column))
        if row < len(self._cell_values)-1:
            adjacent_cells.append((row+1, column))
        if column > 0:
            adjacent_cells.append((row, column-1))
        if column < len(self._cell_values[0])-1:
            adjacent_cells.append((row, column+1))
        return adjacent_cells


    def get_cell_edges(self, row:int, column:int) -> list:
        """Devolve os arestas da célula enviada no argumento"""
        return [
            ('h', row, column),
            ('h', row + 1, column),
            ('v', row, column),
            ('v', row, column + 1),
        ]
    
    
    def print(self):
        """Imprime o tabuleiro no formato indicado no enunciado."""
        for row in range(self._rows):
            row_string = ""
            for col in range(self._cols):
                edges = self.get_cell_edges(row, col)
                val1 = edges[0] in self._edges
                val2 = edges[3] in self._edges
                val3 = edges[1] in self._edges
                val4 = edges[2] in self._edges
                row_string += f"{int(val1)}{int(val2)}{int(val3)}{int(val4)}"
                if col < self._cols - 1:
                    row_string += "\t"
            print(row_string)


    def get_active_edges(self, row:int, column:int) -> list:
        """Devolve o número de arestas ativas"""
        return len(self._edges)


    @staticmethod
    def parse_instance():
        """Lê o test do standard input (stdin) que é passado como argumento
        e retorna uma instância da classe Board.

        Por exemplo:
            $ python3 pipe.py < test-01.txt

            > from sys import stdin
            > line = stdin.readline().split()
        """
        lines = []
        line = stdin.readline().split()
        while line != [] and line != [""]:
            lines.append(line)
            line = stdin.readline().split()
        return Board(lines)


class Slitherlink(Problem):
    def __init__(self, board: Board, gui=None):
        """O construtor especifica o estado inicial."""
        self.board = board
        self.gui = gui
        
        #generate all possible edges
        self.all_edges = []
        for row in range(board._rows + 1):
            for col in range(board._cols):
                self.all_edges.append(('h', row, col))
        for row in range(board._rows):
            for col in range(board._cols + 1):
                self.all_edges.append(('v', row, col))
                
        self.cell_to_edges = {}
        self.numbered_cells_list = []
        for row in range(board._rows):
            for col in range(board._cols):
                self.cell_to_edges[(row, col)] = board.get_cell_edges(row, col)
                val = board._cell_values[row][col]
                if val != '.':
                    self.numbered_cells_list.append(((row, col), int(val)))
                    
        self.vertex_to_edges = defaultdict(list)
        self.edge_to_vertices = {}
        for edge in self.all_edges:
            v1, v2 = self.get_edge_vertices(edge)
            self.edge_to_vertices[edge] = (v1, v2)
            self.vertex_to_edges[v1].append(edge)
            self.vertex_to_edges[v2].append(edge)

        self.edge_priorities = {}
        for edge in self.all_edges:
            score = 0
            for row, col in self.board.get_cells_adjacent_to_edge(edge):
                val = self.board._cell_values[row][col]
                if val != '.':
                    score += int(val) + 1
            self.edge_priorities[edge] = score
        
        initial_state = SlitherlinkState(board)
        if not self.constraint_propagation(initial_state):
            initial_state.is_valid = False
        super().__init__(initial_state)

    def get_edge_vertices(self, edge):
        edge_type, row, col = edge
        if edge_type == 'h':
            return (row, col), (row, col + 1)
        else:
            return (row, col), (row + 1, col)

    def constraint_propagation(self, state: SlitherlinkState, changed_edges=None) -> bool:
        cell_queue = set()
        vertex_queue = set()

        if changed_edges is None:
            cell_queue.update(self.cell_to_edges.keys())
            vertex_queue.update(self.vertex_to_edges.keys())
        else:
            for edge in changed_edges:
                cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                vertex_queue.update(self.edge_to_vertices[edge])

        while cell_queue or vertex_queue:
            while cell_queue:
                row, col = cell_queue.pop()
                targ = self.board._cell_values[row][col]
                if targ == '.':
                    continue

                edges = self.cell_to_edges[(row, col)]
                active = sum(1 for edge in edges if edge in state.active_edges)
                inactive = sum(1 for edge in edges if edge in state.inactive_edges)
                undecided = [
                    edge for edge in edges
                    if edge not in state.active_edges and edge not in state.inactive_edges
                ]
                targ = int(targ)
                if active > targ or 4 - inactive < targ:
                    return False

                if undecided:
                    if active == targ:
                        for edge in undecided:
                            state.inactive_edges.add(edge)
                            cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                            vertex_queue.update(self.edge_to_vertices[edge])
                    elif active + len(undecided) == targ:
                        for edge in undecided:
                            state.active_edges.add(edge)
                            cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                            vertex_queue.update(self.edge_to_vertices[edge])

            if vertex_queue:
                vertex = vertex_queue.pop()
                edges = self.vertex_to_edges[vertex]
                active = sum(1 for edge in edges if edge in state.active_edges)
                inactive = sum(1 for edge in edges if edge in state.inactive_edges)
                undecided = [
                    edge for edge in edges
                    if edge not in state.active_edges and edge not in state.inactive_edges
                ]
                possible = len(edges) - inactive

                if active > 2:
                    return False
                if active == 1 and possible == 1:
                    return False

                if undecided:
                    if active == 2:
                        for edge in undecided:
                            state.inactive_edges.add(edge)
                            cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                            vertex_queue.update(self.edge_to_vertices[edge])
                    elif active == 1 and len(undecided) == 1:
                        edge = undecided[0]
                        state.active_edges.add(edge)
                        cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                        vertex_queue.update(self.edge_to_vertices[edge])
                    elif active == 0 and possible == 1:
                        for edge in undecided:
                            state.inactive_edges.add(edge)
                            cell_queue.update(self.board.get_cells_adjacent_to_edge(edge))
                            vertex_queue.update(self.edge_to_vertices[edge])
            
        return True

    def has_loop_before_final_goal(self, state: SlitherlinkState) -> bool:
        adj_list = defaultdict(list)
        for edge in state.active_edges:
            v1, v2 = self.edge_to_vertices[edge]
            adj_list[v1].append(v2)
            adj_list[v2].append(v1)

        visited = set()
        for start in adj_list:
            if start in visited:
                continue

            stack = [(start, None)]
            curr_loop = set()
            cycle_found = False
            # do the dfs
            while stack:
                vertex, parent = stack.pop()
                if vertex in curr_loop:
                    cycle_found = True
                    continue
                curr_loop.add(vertex)
                visited.add(vertex)
                for neighbor in adj_list[vertex]:
                    if neighbor != parent:
                        stack.append((neighbor, vertex))

            if cycle_found:
                if len(state.active_edges) > len(curr_loop):
                    return True
                for (row, col), targ in self.numbered_cells_list:
                    active = sum(
                        1 for edge in self.cell_to_edges[(row, col)]
                        if edge in state.active_edges
                    )
                    if active != targ:
                        return True

        return False
    
    def actions(self, state: SlitherlinkState):
        """Retorna uma lista de ações que podem ser executadas a
        partir do estado passado como argumento."""
        if not state.is_valid:
            return []
        
        for edges in self.vertex_to_edges.values():
            active = sum(1 for edge in edges if edge in state.active_edges)
            if active == 1:
                undecided = [
                    edge for edge in edges
                    if edge not in state.active_edges and edge not in state.inactive_edges
                ]
                if undecided:
                    edge_to_add = max(undecided, key=lambda edge: self.edge_priorities[edge])
                    return [(edge_to_add, 1), (edge_to_add, 0)]

        best_edge = None
        best_score = -1
        for edge in self.all_edges:
            if edge in state.active_edges or edge in state.inactive_edges:
                continue
            score = self.edge_priorities[edge]
            if score > best_score:
                best_score = score
                best_edge = edge

        if best_edge is None:
            return []
        return [(best_edge, 1), (best_edge, 0)]
                

    def result(self, state: SlitherlinkState, action):
        """Retorna o estado resultante de executar a 'action' sobre
        'state' passado como argumento. A ação a executar deve ser uma
        das presentes na lista obtida pela execução de
        self.actions(state)."""
        edge, value = action
        active_edges = set(state.active_edges)
        inactive_edges = set(state.inactive_edges)
        if value == 1:
            active_edges.add(edge)
        else:
            inactive_edges.add(edge)
        new_state = SlitherlinkState(self.board, active_edges, inactive_edges)
        if not self.constraint_propagation(new_state, changed_edges=[edge]):
            new_state.is_valid = False
        elif value == 1 and self.has_loop_before_final_goal(new_state):
            new_state.is_valid = False
            
        return new_state

    def goal_test(self, state: SlitherlinkState):
        """Retorna True se e só se o estado passado como argumento é
        um estado objetivo. Deve verificar se todas as posições do tabuleiro
        estão preenchidas de acordo com as regras do problema."""
        if not state.is_valid or not state.active_edges:
            return False

        for (row, col), targ in self.numbered_cells_list:
            active = sum(
                1 for edge in self.cell_to_edges[(row, col)]
                if edge in state.active_edges
            )
            if active != targ:
                return False
                
        adj_list = defaultdict(list)
        for edge in state.active_edges:
            v1, v2 = self.edge_to_vertices[edge]
            adj_list[v1].append(v2)
            adj_list[v2].append(v1)

        for adjacent_vertices in adj_list.values():
            #deg(vert) != 2
            if len(adjacent_vertices) != 2:
                return False

        #dfs
        visited = set()
        stack = [next(iter(adj_list))]
        while stack:
            vertex = stack.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            for neighbor in adj_list[vertex]:
                if neighbor not in visited:
                    stack.append(neighbor)

        return len(visited) == len(adj_list)

    def h(self, node: Node):
        """Função heuristica utilizada para a procura A*."""
        #not needed
        pass


if __name__ == "__main__":
    # TODO:
    # Ler o ficheiro do standard input,
    # Usar uma técnica de procura para resolver a instância,
    # Retirar a solução a partir do nó resultante,
    # Imprimir para o standard output no formato indicado.
    board = Board.parse_instance()
    problem = Slitherlink(board)
    goal_state = depth_first_tree_search(problem)

    if goal_state is not None:
        goal_state.state.board._edges = goal_state.state.active_edges
        goal_state.state.board.print()
    else:
        print("No solution")
