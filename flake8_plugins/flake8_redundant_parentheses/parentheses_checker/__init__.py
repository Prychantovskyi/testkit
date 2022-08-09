import ast
import importlib.metadata
from typing import (
    Any,
    Generator,
    List,
    Tuple,
    Type,
)


class Checker:
    def __init__(self, vals, tree):
        self.problems: List[Tuple[int, int, str]] = []
        self.vals = vals
        self.tree = tree
        assert isinstance(self.tree, ast.Module)

    @staticmethod
    def _node_in_parens(node, parens_coords):
        open_, _, _, close = parens_coords
        node_start = (node.lineno, node.col_offset)
        node_end = (node.end_lineno, node.end_col_offset)
        return node_start >= open_ and node_end <= close

    def check(self) -> None:
        msg = "PAR001: Too many parentheses"
        # exceptions made for parentheses that are not strictly necessary
        # but help readability
        exceptions = []
        bin_exc = (ast.BinOp, ast.BoolOp, ast.UnaryOp, ast.Compare, ast.Await)
        for node in ast.walk(self.tree):
            if isinstance(node, bin_exc):
                for child in ast.iter_child_nodes(node):
                    if not isinstance(child, bin_exc):
                        continue
                    for val in self.vals:
                        if self._node_in_parens(node, val):
                            break
                        if self._node_in_parens(child, val) \
                           and val not in exceptions:
                            exceptions.append(val)
                            break

            if isinstance(node, ast.Assign):
                for targ in node.targets:
                    if not isinstance(targ, ast.Tuple):
                        continue
                    for elts in targ.elts:
                        tuple_coords = (targ.lineno, targ.col_offset)
                        elts_coords = (elts.lineno, elts.col_offset)
                        if tuple_coords < elts_coords:
                            for val in self.vals:
                                if (
                                    val[0] == tuple_coords
                                    and val not in exceptions
                                ):
                                    exceptions.append(val)
                                    break
                            self.problems.append((
                                node.lineno, node.col_offset,
                                "PAR002: Dont use parentheses for "
                                "unpacking"
                            ))
                        break

            for node_tup in ast.iter_child_nodes(node):
                if isinstance(node_tup, ast.Tuple):
                    if node_tup.end_col_offset - node.end_col_offset == 0:
                        for val in self.vals:
                            if val not in exceptions:
                                exceptions.append(val)
                                break
                        break

        for val in self.vals:
            if val in exceptions:
                continue
            self.problems.append((*val[0], msg))


class Plugin:
    name = __name__
    version = importlib.metadata.version("flake8_redundant_parentheses")

    def __init__(self, tree: ast.AST, read_lines, file_tokens):
        self.vals = []
        self._lines_list = "".join(read_lines())
        self.file_token = list(file_tokens)
        self._tree = tree
        self.dump_tree = ast.dump(tree)
        self.parens_coords = find_parens_coords(self.file_token)
        for coords in self.parens_coords:
            if check_trees(self._lines_list, self.dump_tree, coords):
                self.vals.append(coords)

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        if not self.vals:
            return
        checker = Checker(self.vals, self._tree)
        checker.check()
        for line, col, msg in checker.problems:
            yield line, col, msg, type(self)


def find_parens_coords(token):
    open_list = ["[", "{", "("]
    close_list = ["]", "}", ")"]
    opening_stack = []
    parentheses_pairs = []
    last_line = -1
    for i in range(len(token)):
        first_in_line = last_line != token[i].start[0]
        last_line = token[i].end[0]
        if token[i].type == 54:
            if token[i].string in open_list:
                if not first_in_line:
                    opening_stack.append([token[i].start, token[i].end[1],
                                          " ", token[i].string])
                    continue
                if token[i + 1].start[0] == token[i].end[0]:
                    opening_stack.append([token[i].start,
                                          token[i + 1].start[1], "",
                                          token[i].string])
                    continue
                # there is only this opening parenthesis on this line
                opening_stack.append([token[i].start, len(token[i].line) - 2,
                                      "", token[i].string])

            if token[i].string in close_list:
                opening = opening_stack.pop()
                assert (open_list.index(opening[3])
                        == close_list.index(token[i].string))
                parentheses_pairs.append(
                    [*opening[0:3], token[i].start]
                )

    return parentheses_pairs


def check_trees(source_code, start_tree, parens_coords):
    """Check if parentheses are redundant.

    Replace a pair of parentheses with a blank string and check if the
    resulting AST is still the same.
    """
    open_, space, replacement, close = parens_coords
    lines = source_code.split("\n")
    lines[open_[0] - 1] = (lines[open_[0] - 1][:open_[1]]
                           + replacement
                           + lines[open_[0] - 1][space:])
    shift = 0
    if open_[0] == close[0]:
        shift -= (space - open_[1]) - len(replacement)
    lines[close[0] - 1] = (lines[close[0] - 1][:close[1] + shift]
                           + " " + lines[close[0] - 1][close[1] + 1 + shift:])
    code_without_parens = "\n".join(lines)
    try:
        tree = ast.parse(code_without_parens)
    except (ValueError, SyntaxError):
        return False
    if tree is not False and ast.dump(tree) == start_tree:
        return True
    else:
        return False
