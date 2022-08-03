import ast
import importlib.metadata
from typing import Any
from typing import Generator
from typing import List
from typing import Tuple
from typing import Type


class Visitor(ast.NodeVisitor):
    def __init__(self, vals, tree):
        self.problems: List[Tuple[int, int, str]] = []
        self.vals = vals
        self.tree = tree

    def visit_Module(self, node: ast.Module) -> None:
        msg = 'PAR001: Too many parentheses'
        ex = []
        for node_ in ast.walk(self.tree):
            if isinstance(node_, ast.BinOp) or isinstance(node_, ast.BoolOp):
                for node_op in ast.iter_child_nodes(node_):
                    if isinstance(node_op, ast.BinOp) or isinstance(node_op, ast.BoolOp):
                        ex.append([node_op.col_offset - 1, node_op.end_col_offset])

            if isinstance(node_, ast.Assign):
                for targ in node_.targets:
                    if isinstance(targ, ast.Tuple):
                        self.problems.append((node_.lineno, node_.col_offset,
                                              'PAR002: Dont use parentheses for unpacking'))
                        continue

            for node_tup in ast.iter_child_nodes(node_):
                if isinstance(node_tup, ast.Tuple):
                    for node__ in node_tup.elts:
                        if node_tup.end_col_offset - node__.end_col_offset != 2:
                            self.problems.append((node_.lineno, node_.col_offset,
                                                 'PAR003: Use parentheses for tuple literal'))
                            continue
                        if node_tup.end_col_offset - node_.end_col_offset == 0:
                            ex.append([node_tup.col_offset, node_tup.end_col_offset - 1])
                            continue

        for node_ in node.body:
            if ex:
                for j in ex:
                    for i in self.vals:
                        if i is not False and i != j:
                            self.problems.append((node_.lineno, node_.col_offset, msg))
                        continue

            elif not self.vals:
                break

            elif not self.problems:
                for j in self.vals:
                    if j is False:
                        continue
                    else:
                        self.problems.append((node_.lineno, node_.col_offset, msg))
                        break
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib.metadata.version(__name__)

    def __init__(self, tree: ast.AST, read_lines, file_tokens):
        self._tree = tree
        self.vals = []
        self.dump_tree = ast.dump(tree)
        self.dict = check(list(file_tokens))
        self._lines_list = "".join(read_lines)
        for i in self.dict.values():
            self.vals.append(check_trees(self._lines_list, self.dump_tree, i))

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor(self.vals, self._tree)
        visitor.visit(self._tree)
        for line, col, MSG in visitor.problems:
            yield line, col, MSG, type(self)


def check(token):
    open_cord_dict = {}
    close_cord_dict = {}
    result_ = {}
    open_list = ["[", "{", "("]
    close_list = ["]", "}", ")"]
    num = 0
    col = 0
    for i in token:
        if i.type == 54:
            if i.string in open_list:
                open_cord_dict.update({col: [i.start, i.string]})
            if i.string in close_list:
                close_cord_dict.update({col: [i.start, i.string]})
            col += 1

    rev_open_dict = dict(reversed(open_cord_dict.items()))
    for y in rev_open_dict.keys():
        for j in close_cord_dict.keys():
            if open_list.index(rev_open_dict.get(y)[1]) == close_list.index(close_cord_dict.get(j)[1]):
                result_.update({"{number} {type}".format
                                (number=num, type=rev_open_dict.get(y)[1]):
                                    [rev_open_dict.get(y)[0], close_cord_dict.get(j)[0]]})
                close_cord_dict.pop(j)
                num += 1
                break
    return result_


def check_trees(list_, start_tree, u):
    list__ = list_.split("\n")
    list__[u[0][0] - 1] = list__[u[0][0] - 1][:u[0][1]] + " " + list__[u[0][0] - 1][u[0][1] + 1:]
    list__[u[1][0] - 1] = list__[u[1][0] - 1][:u[1][1]] + " " + list__[u[1][0] - 1][u[1][1] + 1:]
    list__ = "\n".join(list__)
    try:
        tree = ast.parse(list__)
        if ast.dump(tree) == start_tree:
            return [u[0][1], u[1][1]]
        else:
            return False
    except:
        return False
