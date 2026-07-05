from typing import Optional, List, Dict
from dataclasses import dataclass
from ast_nodes import *
import string


@dataclass
class Match:
    start: int
    end: int
    text: str
    groups: Dict[int, Optional[str]]  # group_number -> captured text

    def group(self, n: int = 0) -> Optional[str]:
        if n == 0:
            return self.text
        return self.groups.get(n)


class Matcher:
    def __init__(self, ast: ASTNode, flags: Optional[Dict[str, bool]] = None):
        self.ast = ast
        self.flags = flags or {}

        # Flags
        self.ignore_case = self.flags.get("ignorecase", False)
        self.multiline = self.flags.get("multiline", False)
        self.dotall = self.flags.get("dotall", False)

        # State during matching
        self.text = ""
        self.length = 0
        self.captures: Dict[int, Optional[str]] = {}

        self._init_char_classes()

    def _init_char_classes(self):
        self.digit_chars = set("0123456789")
        self.word_chars = set(string.ascii_letters + string.digits + "_")
        self.whitespace_chars = set(" \t\n\r\f\v")

    def match(self, text: str, start: int = 0) -> Optional[Match]:
        self.text = text
        self.length = len(text)
        self.captures = {}

        end_pos = self._match_node(self.ast, start)

        if end_pos is not None:
            return Match(
                start=start,
                end=end_pos,
                text=text[start:end_pos],
                groups=self.captures.copy(),
            )

        return None

    def search(self, text: str) -> Optional[Match]:
        self.text = text
        self.length = len(text)

        for start in range(len(text) + 1):
            self.captures = {}
            end_pos = self._match_node(self.ast, start)

            if end_pos is not None:
                return Match(
                    start=start,
                    end=end_pos,
                    text=text[start:end_pos],
                    groups=self.captures.copy(),
                )

        return None

    def findall(self, text: str) -> List[Match]:
        self.text = text
        self.length = len(text)
        matches = []
        pos = 0

        while pos <= len(text):
            self.captures = {}
            end_pos = self._match_node(self.ast, pos)

            if end_pos is not None:
                match = Match(
                    start=pos,
                    end=end_pos,
                    text=text[pos:end_pos],
                    groups=self.captures.copy(),
                )
                matches.append(match)

                pos = end_pos if end_pos > pos else pos + 1
            else:
                pos += 1

        return matches

    def _match_node(self, node: ASTNode, pos: int) -> Optional[int]:
        if isinstance(node, CharNode):
            return self._match_char(node, pos)
        elif isinstance(node, DotNode):
            return self._match_dot(node, pos)
        elif isinstance(node, CharClassNode):
            return self._match_char_class(node, pos)
        elif isinstance(node, PredefinedClassNode):
            return self._match_predefined_class(node, pos)
        elif isinstance(node, QuantifierNode):
            return self._match_quantifier(node, pos)
        elif isinstance(node, ConcatNode):
            return self._match_concat(node, pos)
        elif isinstance(node, AlternationNode):
            return self._match_alternation(node, pos)
        elif isinstance(node, GroupNode):
            return self._match_group(node, pos)
        elif isinstance(node, NonCapturingGroupNode):
            return self._match_node(node.child, pos)
        elif isinstance(node, BackreferenceNode):
            return self._match_backref(node, pos)
        elif isinstance(node, AnchorNode):
            return self._match_anchor(node, pos)
        elif isinstance(node, LookaheadNode):
            return self._match_lookahead(node, pos)
        elif isinstance(node, LookbehindNode):
            return self._match_lookbehind(node, pos)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def _match_char(self, node: CharNode, pos: int) -> Optional[int]:
        if pos >= self.length:
            return None

        text_char = self.text[pos]
        pattern_char = node.char

        if self.ignore_case:
            text_char = text_char.lower()
            pattern_char = pattern_char.lower()

        if text_char == pattern_char:
            return pos + 1

        return None

    def _match_dot(self, node: DotNode, pos: int) -> Optional[int]:
        if pos >= self.length:
            return None

        char = self.text[pos]

        if not self.dotall and char == "\n":
            return None

        return pos + 1

    def _match_char_class(self, node: CharClassNode, pos: int) -> Optional[int]:
        if pos >= self.length:
            return None

        char = self.text[pos]
        chars = node.chars

        if self.ignore_case:
            char = char.lower()
            chars = set(c.lower() for c in chars)

        in_class = char in chars

        if in_class != node.negated:
            return pos + 1

        return None

    def _match_predefined_class(
        self, node: PredefinedClassNode, pos: int
    ) -> Optional[int]:
        if pos >= self.length:
            return None

        char = self.text[pos]
        matched = False

        if node.class_type == "d":
            matched = char in self.digit_chars
        elif node.class_type == "D":
            matched = char not in self.digit_chars
        elif node.class_type == "w":
            matched = char in self.word_chars
        elif node.class_type == "W":
            matched = char not in self.word_chars
        elif node.class_type == "s":
            matched = char in self.whitespace_chars
        elif node.class_type == "S":
            matched = char not in self.whitespace_chars

        if matched:
            return pos + 1

        return None

    def _match_quantifier(self, node: QuantifierNode, pos: int) -> Optional[int]:
        matches = []
        current_pos = pos
        count = 0

        while True:
            if node.max_count is not None and count >= node.max_count:
                break

            next_pos = self._match_node(node.child, current_pos)

            if next_pos is None or next_pos == current_pos:
                break

            count += 1
            current_pos = next_pos
            matches.append(current_pos)

        valid_matches = [pos] if node.min_count == 0 else []
        valid_matches.extend(
            [m for i, m in enumerate(matches, 1) if i >= node.min_count]
        )

        if not valid_matches:
            return None

        if node.greedy:
            return valid_matches[-1]
        else:
            return valid_matches[0]

    def _match_concat(self, node: ConcatNode, pos: int) -> Optional[int]:
        if not node.children:
            return pos

        return self._match_concat_recursive(node.children, 0, pos)

    def _match_concat_recursive(
        self, children: List[ASTNode], child_idx: int, pos: int
    ) -> Optional[int]:
        if child_idx >= len(children):
            return pos

        child = children[child_idx]

        if isinstance(child, QuantifierNode):
            matches = []
            current_pos = pos
            count = 0

            while True:
                if child.max_count is not None and count >= child.max_count:
                    break

                next_pos = self._match_node(child.child, current_pos)

                if next_pos is None or next_pos == current_pos:
                    break

                count += 1
                current_pos = next_pos
                matches.append(current_pos)

            valid_matches = [pos] if child.min_count == 0 else []
            valid_matches.extend(
                [m for i, m in enumerate(matches, 1) if i >= child.min_count]
            )

            if not valid_matches:
                return None

            if child.greedy:
                valid_matches.reverse()

            for match_end in valid_matches:
                result = self._match_concat_recursive(
                    children, child_idx + 1, match_end
                )
                if result is not None:
                    return result

            return None
        else:
            next_pos = self._match_node(child, pos)

            if next_pos is None:
                return None

            return self._match_concat_recursive(children, child_idx + 1, next_pos)

    def _match_alternation(self, node: AlternationNode, pos: int) -> Optional[int]:
        for alt in node.alternatives:
            end_pos = self._match_node(alt, pos)

            if end_pos is not None:
                return end_pos

        return None

    def _match_group(self, node: GroupNode, pos: int) -> Optional[int]:
        old_capture = self.captures.get(node.group_number)

        end_pos = self._match_node(node.child, pos)

        if end_pos is not None:
            self.captures[node.group_number] = self.text[pos:end_pos]
            return end_pos
        else:
            if old_capture is not None:
                self.captures[node.group_number] = old_capture
            elif node.group_number in self.captures:
                del self.captures[node.group_number]
            return None

    def _match_backref(self, node: BackreferenceNode, pos: int) -> Optional[int]:
        captured = self.captures.get(node.group_number)

        if captured is None:
            return None

        end_pos = pos + len(captured)

        if end_pos > self.length:
            return None

        text_slice = self.text[pos:end_pos]

        if self.ignore_case:
            if text_slice.lower() == captured.lower():
                return end_pos
        else:
            if text_slice == captured:
                return end_pos

        return None

    def _match_anchor(self, node: AnchorNode, pos: int) -> Optional[int]:
        if node.anchor_type == "^":
            if pos == 0:
                return pos
            if self.multiline and pos > 0 and self.text[pos - 1] == "\n":
                return pos
            return None
        elif node.anchor_type == "$":
            if pos == self.length:
                return pos
            if self.multiline and pos < self.length and self.text[pos] == "\n":
                return pos
            return None
        elif node.anchor_type == "b":
            before_is_word = pos > 0 and self.text[pos - 1] in self.word_chars
            after_is_word = pos < self.length and self.text[pos] in self.word_chars

            if before_is_word != after_is_word:
                return pos
            return None

        elif node.anchor_type == "B":
            before_is_word = pos > 0 and self.text[pos - 1] in self.word_chars
            after_is_word = pos < self.length and self.text[pos] in self.word_chars

            if before_is_word == after_is_word:
                return pos
            return None

        return None

    def _match_lookahead(self, node: LookaheadNode, pos: int) -> Optional[int]:
        end_pos = self._match_node(node.child, pos)

        matched = end_pos is not None

        if matched == node.positive:
            return pos

        return None

    def _match_lookbehind(self, node: LookbehindNode, pos: int) -> Optional[int]:
        found_match = False
        for start in range(pos, -1, -1):
            end_pos = self._match_node(node.child, start)

            if end_pos == pos:
                found_match = True
                break

        if found_match == node.positive:
            return pos

        return None