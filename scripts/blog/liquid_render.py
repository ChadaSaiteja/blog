"""A small Liquid renderer for the Flask dev server.

Jekyll is the real build. This module exists so that
``python scripts/blog/server.py`` renders the *same* layouts with the *same*
includes and the *same* _data/blog_style.yml, instead of the earlier regex
approximation that quietly produced broken HTML as soon as the layouts used
``{% assign %}``, nested ``{% for %}`` or ``{% include %}`` with arguments.

Supported:
  {{ output }} with filters and ``{{-`` / ``-}}`` whitespace control
  {% if %} / {% elsif %} / {% else %} / {% endif %}
  {% unless %}
  {% case %} / {% when %}
  {% assign var = expr %}
  {% for x in list %} ... {% else %} ... {% endfor %} with limit/offset/forloop
  {% include name.html key=value %}
  {% comment %} ... {% endcomment %}
  {{- ... -}} and {%- ... -%} whitespace trimming

Deliberately unsupported constructs are recorded on the renderer instance
(``unsupported``) instead of being dropped, so a preview can say out loud that
it is not faithful rather than quietly losing markup.
"""

import json
import os
import re
from datetime import date, datetime

TOKEN_RE = re.compile(r"\{%(-?)(.*?)(-?)%\}|\{\{(-?)(.*?)(-?)\}\}", re.DOTALL)
TAG_RE = re.compile(r"^(\w+)\s*(.*)$", re.DOTALL)

# The 62 filters Shopify Liquid ships. A template may only use these plus the
# handful Jekyll adds. This allowlist exists because the renderer used to accept
# any filter name, which silently hid two non-portable ones (`push` and `index`)
# that the GitHub Pages build does not have. An unknown filter now shows up in
# `unsupported` instead of quietly returning nothing.
STANDARD_FILTERS = {
    "abs", "append", "at_least", "at_most", "base64_decode", "base64_encode",
    "capitalize", "ceil", "compact", "concat", "date", "default", "divided_by",
    "downcase", "escape", "escape_once", "escapejs", "find", "find_index",
    "first", "floor", "has", "join", "last", "lstrip", "map", "minus", "modulo",
    "newline_to_br", "plus", "prepend", "reject", "remove", "remove_first",
    "remove_last", "replace", "replace_first", "replace_last", "reverse", "round",
    "rstrip", "safe", "size", "slice", "sort", "sort_natural", "split", "squish",
    "strip", "strip_html", "strip_newlines", "sum", "times", "truncate",
    "truncatewords", "uniq", "upcase", "url_decode", "url_encode", "where",
}

# Jekyll ships these on top of standard Liquid.
JEKYLL_FILTERS = {
    "absolute_url", "date_to_string", "date_to_long_string",
    "date_to_xmlschema", "group_by", "jsonify", "markdownify", "number_of_words",
    "relative_url", "sassify", "scssify", "slugify", "sort_natural",
    "where_exp", "xml_escape",
}

ALLOWED_FILTERS = STANDARD_FILTERS | JEKYLL_FILTERS

TRUTHY = object()

BLOCK_ENDERS = {"endif", "endunless", "endfor", "endcase", "endcomment"}

class LiquidError(Exception):
    pass


# ----------------------------------------------------------------------
# expression helpers
# ----------------------------------------------------------------------
def split_top_level(source, separator):
    """Split on `separator` outside quotes, brackets and parens."""
    parts = []
    depth = 0
    quote = None
    buffer = []
    index = 0
    sep_len = len(separator)

    while index < len(source):
        char = source[index]

        if quote:
            buffer.append(char)
            if char == "\\" and index + 1 < len(source):
                buffer.append(source[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue

        if char in "\"'":
            quote = char
            buffer.append(char)
        elif char in "[({":
            depth += 1
            buffer.append(char)
        elif char in "])}":
            depth -= 1
            buffer.append(char)
        elif depth == 0 and source.startswith(separator, index):
            parts.append("".join(buffer))
            buffer = []
            index += sep_len
            continue
        else:
            buffer.append(char)
        index += 1

    parts.append("".join(buffer))
    return parts


def split_filters(source):
    return [p.strip() for p in split_top_level(source, "|") if p.strip()]


def find_top_level(source, needle):
    """Index of `needle` outside quotes/brackets, or -1."""
    depth = 0
    quote = None
    index = 0
    while index < len(source):
        char = source[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "[({":
            depth += 1
        elif char in "])}":
            depth -= 1
        elif depth == 0 and source.startswith(needle, index):
            return index
        index += 1
    return -1


# ----------------------------------------------------------------------
# values
# ----------------------------------------------------------------------
def to_liquid_list(value):
    """Ruby-ish enumerables, so a dict iterates as [key, value] pairs."""
    if isinstance(value, dict):
        return [[k, v] for k, v in value.items()]
    if isinstance(value, (list, tuple)):
        return list(value)
    if value is None:
        return []
    return [value]


def is_truthy(value):
    return value is not None and value is not False


class LiquidRenderer:
    def __init__(self, workspace):
        self.workspace = workspace
        self.includes_dir = os.path.join(workspace, "_includes")
        self.unsupported = []

    # -- public ------------------------------------------------------
    def render(self, source, scopes):
        self.unsupported = []
        tokens = self._tokenize(source)
        nodes, _ = self._parse(tokens, 0, set())
        return self._render_nodes(nodes, [dict(s) for s in scopes])

    # -- tokenizer ---------------------------------------------------
    def _tokenize(self, text):
        tokens = []
        position = 0
        for match in TOKEN_RE.finditer(text):
            if match.start() > position:
                tokens.append(["text", text[position:match.start()], False, False])
            if match.group(2) is not None:
                tokens.append(["tag", match.group(2).strip(), match.group(1) == "-", match.group(3) == "-"])
            else:
                tokens.append(["out", match.group(5).strip(), match.group(4) == "-", match.group(6) == "-"])
            position = match.end()
        if position < len(text):
            tokens.append(["text", text[position:], False, False])

        for index, token in enumerate(tokens):
            if not (token[2] or token[3]):
                continue
            if token[2] and index > 0 and tokens[index - 1][0] == "text":
                tokens[index - 1][1] = tokens[index - 1][1].rstrip()
            if token[3] and index + 1 < len(tokens) and tokens[index + 1][0] == "text":
                tokens[index + 1][1] = tokens[index + 1][1].lstrip()
        return tokens

    # -- parser ------------------------------------------------------
    def _tag_at(self, tokens, index):
        """(name, args) for a tag token, or (None, None)."""
        if index >= len(tokens) or tokens[index][0] != "tag":
            return None, None
        match = TAG_RE.match(tokens[index][1])
        if not match:
            return None, None
        return match.group(1), match.group(2).strip()

    def _parse(self, tokens, index, stops):
        """Parse nodes until one of `stops` is reached.

        The terminating tag is left unconsumed so the caller can inspect it and
        decide whether to keep going (elsif / else / when) or finish.
        """
        nodes = []
        while index < len(tokens):
            token = tokens[index]
            kind, value = token[0], token[1]

            if kind in ("text", "out"):
                nodes.append((kind, value))
                index += 1
                continue

            name, args = self._tag_at(tokens, index)
            if name is None:
                index += 1
                continue

            if name in stops:
                return nodes, index

            if name in ("if", "unless"):
                node, index = self._parse_conditional(
                    tokens, index + 1, args, negate=(name == "unless")
                )
                nodes.append(node)
                continue

            if name == "case":
                node, index = self._parse_case(tokens, index + 1)
                nodes.append(node)
                continue

            if name == "for":
                node, index = self._parse_for(tokens, index + 1)
                nodes.append(node)
                continue

            if name == "comment":
                _, index = self._parse(tokens, index + 1, {"endcomment"})
                index += 1
                continue

            if name == "assign":
                target, _, expression = args.partition("=")
                nodes.append(("assign", target.strip(), expression.strip()))
                index += 1
                continue

            if name == "include":
                nodes.append(("include", args))
                index += 1
                continue

            if name in ("break", "continue"):
                nodes.append((name,))
                index += 1
                continue

            self.unsupported.append("{{% {} %}}".format(name))
            index += 1
        return nodes, index

    def _parse_conditional(self, tokens, index, condition, negate=False):
        enders = {"endif", "endunless"}
        branches = []
        else_body = []

        while True:
            body, index = self._parse(tokens, index, enders | {"elsif", "elif", "else"})
            branches.append((condition, body))

            name, args = self._tag_at(tokens, index)
            if name in ("elsif", "elif"):
                condition = args
                index += 1
                continue
            if name == "else":
                else_body, index = self._parse(tokens, index + 1, enders)
            index += 1
            break

        return ("unless" if negate else "if", branches, else_body), index

    def _parse_case(self, tokens, index):
        _, subject = self._tag_at(tokens, index - 1)
        whens = []
        else_body = []
        current = None
        buffer = []

        def flush():
            if current is not None:
                whens.append((list(current), buffer))

        while True:
            body, index = self._parse(tokens, index, {"endcase", "when", "else"})
            if current is None:
                else_body.extend(body)
            else:
                buffer.extend(body)

            name, args = self._tag_at(tokens, index)
            if name == "when":
                flush()
                # Keep the quotes: these are literals to evaluate, not variables.
                current = [v.strip() for v in split_top_level(args, ",") if v.strip()]
                buffer = []
                index += 1
                continue
            if name == "else":
                flush()
                current = None
                else_body = []
                index += 1
                continue
            if name == "endcase" or name is None:
                flush()
                index += 1
                break

        return ("case", subject, whens, else_body), index

    def _parse_for(self, tokens, index):
        _, args = self._tag_at(tokens, index - 1)
        head, _, tail = args.partition(" in ")
        variable = head.strip()

        # Everything that is not a known loop option belongs to the collection
        # expression, which may itself carry filters:
        #   {% for x in list limit: 2 %}   vs   {% for c in "ab" | split: "" %}
        collection_parts = []
        options = {}
        for part in split_top_level(tail, ","):
            part = part.strip()
            if not part:
                continue
            option_name, separator, option_value = part.partition(":")
            if separator and option_name.strip() in ("limit", "offset", "reversed"):
                options[option_name.strip()] = option_value.strip()
            else:
                collection_parts.append(part)
        collection = " ".join(collection_parts)

        body, index = self._parse(tokens, index, {"endfor", "else"})
        else_body = []
        name, _ = self._tag_at(tokens, index)
        if name == "else":
            else_body, index = self._parse(tokens, index + 1, {"endfor"})
        index += 1

        return ("for", (variable, collection, options), body, else_body), index

    # -- renderer ----------------------------------------------------
    def _render_nodes(self, nodes, scopes, root=None):
        if root is None:
            root = scopes[0]
        out = []
        for node in nodes:
            kind = node[0]
            if kind == "text":
                out.append(node[1])
            elif kind == "out":
                out.append(self._stringify(self._eval_output(node[1], scopes)))
            elif kind == "assign":
                self._assign(node[1], node[2], scopes, root)
            elif kind in ("if", "unless"):
                negate = kind == "unless"
                hit = False
                for condition, body in node[1]:
                    if negate:
                        if not self._condition(condition, scopes):
                            out.append(self._render_nodes(body, scopes, root))
                            hit = True
                            break
                    elif self._condition(condition, scopes):
                        out.append(self._render_nodes(body, scopes, root))
                        hit = True
                        break
                if not hit:
                    out.append(self._render_nodes(node[2], scopes, root))
            elif kind == "case":
                subject = self._eval(node[1], scopes)
                matched = False
                for values, body in node[2]:
                    if any(self._stringify(self._eval(v, scopes)) == self._stringify(subject) for v in values):
                        out.append(self._render_nodes(body, scopes, root))
                        matched = True
                        break
                if not matched:
                    out.append(self._render_nodes(node[3], scopes, root))
            elif kind == "for":
                out.append(self._render_for(node[1], node[2], node[3], scopes, root))
            elif kind == "include":
                out.append(self._render_include(node[1], scopes, root))
            elif kind in ("break", "continue"):
                break
        return "".join(out)

    def _render_for(self, spec, body, else_body, scopes, root):
        variable, collection, options = spec
        items = to_liquid_list(self._eval_output(collection, scopes))

        if "limit" in options:
            limit = self._eval(options["limit"], scopes)
            if limit is not None:
                items = items[: int(limit)]
        if "offset" in options:
            offset = self._eval(options["offset"], scopes)
            if offset is not None:
                items = items[int(offset):]
        if options.get("reversed"):
            items = list(reversed(items))

        if not items:
            return self._render_nodes(else_body, scopes, root)

        total = len(items)
        rendered = []
        for position, item in enumerate(items):
            # The loop variable lives in its own scope layered on top of the
            # real one, so outer variables stay visible and {% assign %} inside
            # the loop still writes to the root.
            loop_scope = {
                variable: item,
                "forloop": {
                    "index": position + 1,
                    "index0": position,
                    "rindex": total - position,
                    "rindex0": total - position - 1,
                    "first": position == 0,
                    "last": position == total - 1,
                    "length": total,
                },
            }
            rendered.append(self._render_nodes(body, [loop_scope] + list(scopes), root))
        return "".join(rendered)

    def _render_include(self, args, scopes, root):
        parts = split_top_level(args, " ")
        if not parts:
            return ""
        name = parts[0].strip().strip("\"'")
        kwargs = {}
        for part in parts[1:]:
            key, sep, value = part.partition("=")
            if sep:
                kwargs[key.strip()] = self._eval(value.strip(), scopes)

        path = os.path.join(self.includes_dir, name)
        if not os.path.exists(path):
            self.unsupported.append("{{% include {} %}} (not found)".format(name))
            return "<!-- include {} not found -->".format(name)

        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()

        include_scope = dict(scopes[0])
        include_scope["include"] = kwargs
        return self.render(source, [include_scope] + list(scopes[1:]))

    def _assign(self, target, expression, scopes, root):
        # Liquid writes assign to the outermost scope, so a value set inside a
        # {% for %} survives the loop. The right-hand side is a full output
        # expression, so filters apply: {% assign n = list | size %}.
        root[target] = self._eval_output(expression, scopes)

    # -- evaluation --------------------------------------------------
    def _stringify(self, value):
        if value is None or value is False:
            return ""
        if value is True:
            return "true"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, (list, tuple)):
            return "".join(str(v) for v in value)
        return str(value)

    def _eval_output(self, source, scopes):
        parts = split_filters(source)
        value = self._eval(parts[0], scopes)
        for stage in parts[1:]:
            value = self._apply_filter(stage, value, scopes)
        return value

    def _apply_filter(self, stage, value, scopes):
        name, _, argument_text = stage.partition(":")
        name = name.strip()
        args = [self._eval(a.strip(), scopes) for a in split_top_level(argument_text, ",")] if argument_text.strip() else []

        if name not in ALLOWED_FILTERS:
            # Liquid has no `push` and no `index`. Accepting them here is how
            # they got into the templates in the first place and then broke the
            # real build, so report rather than guess.
            self.unsupported.append(
                "filter: {} (not in the standard Liquid set)".format(name)
            )
            return value

        if name == "default":
            fallback = args[0] if args else ""
            return fallback if value in (None, False) else value
        if name == "escape":
            return (self._stringify(value)
                    .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    .replace('"', "&quot;"))
        if name == "downcase":
            return self._stringify(value).lower()
        if name == "upcase":
            return self._stringify(value).upper()
        if name == "strip":
            return self._stringify(value).strip()
        if name == "size":
            if isinstance(value, (list, tuple, dict, str)):
                return len(value)
            return len(self._stringify(value))
        if name == "join":
            sep = self._stringify(args[0]) if args else " "
            return sep.join(self._stringify(v) for v in to_liquid_list(value))
        if name == "first":
            items = to_liquid_list(value)
            return items[0] if items else None
        if name == "last":
            items = to_liquid_list(value)
            return items[-1] if items else None
        if name == "plus":
            return self._number(value) + self._number(args[0])
        if name == "minus":
            return self._number(value) - self._number(args[0])
        if name == "times":
            return self._number(value) * self._number(args[0])
        if name == "modulo":
            divisor = self._number(args[0])
            return self._number(value) % divisor if divisor else 0
        if name == "prepend":
            return self._stringify(args[0]) + self._stringify(value)
        if name == "append":
            return self._stringify(value) + self._stringify(args[0])
        if name == "replace":
            return self._stringify(value).replace(self._stringify(args[0]), self._stringify(args[1]))
        if name == "slice":
            text = self._stringify(value)
            if len(args) == 1:
                return text[int(args[0]): int(args[0]) + 1]
            return text[int(args[0]): int(args[0]) + int(args[1])]
        if name == "split":
            text = self._stringify(value)
            separator = self._stringify(args[0]) if args else ""
            if text == "":
                return []
            if separator == "":
                return list(text)
            return text.split(separator)
        if name == "index":
            items = to_liquid_list(value)
            target = self._stringify(args[0])
            for position, item in enumerate(items):
                if self._stringify(item) == target:
                    return position
            return None
        if name == "truncatewords":
            words = self._stringify(value).split()
            count = int(args[0]) if args else 15
            return " ".join(words[:count]) + ("..." if len(words) > count else "")
        if name == "date":
            return self._format_date(value, self._stringify(args[0]) if args else "%Y-%m-%d")
        if name == "relative_url":
            base = scopes[0].get("site", {}).get("baseurl", "")
            return self._join_url(base, value)
        if name == "absolute_url":
            return self._join_url(scopes[0].get("site", {}).get("url", ""), value)
        if name == "json":
            return json.dumps(value, default=str)
        if name == "where_exp":
            item_name = self._stringify(args[0])
            expression = self._stringify(args[1]) if len(args) > 1 else ""
            return self.apply_where_exp(to_liquid_list(value), item_name, expression, scopes)

        self.unsupported.append("filter: {}".format(name))
        return value

    def _join_url(self, base, value):
        text = self._stringify(value)
        base = base or ""
        if text.startswith(("http://", "https://")):
            return text
        return "{}/{}".format(base.rstrip("/"), text.lstrip("/")) if base else "/" + text.lstrip("/")

    def _number(self, value):
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        try:
            return int(str(value).strip())
        except ValueError:
            try:
                return float(str(value).strip())
            except ValueError:
                return 0

    def _format_date(self, value, fmt):
        parsed = value
        if isinstance(parsed, str):
            for pattern in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(parsed.replace("Z", "+0000"), pattern)
                    break
                except ValueError:
                    continue
        if isinstance(parsed, (datetime, date)):
            return parsed.strftime(fmt)
        return self._stringify(value)

    def _lookup(self, path, scopes):
        # Normalise bracket indexing to dotted form so that pair[0] and
        # hashes['key'] resolve the same way as pair.0 and hashes.key.
        normalized = re.sub(r"\[\s*(.*?)\s*\]", r".\1", path)
        parts = [part for part in normalized.split(".") if part != ""]
        if not parts:
            return None

        value = None
        for scope in reversed(scopes):
            if parts[0] in scope:
                value = scope[parts[0]]
                break
        else:
            return None

        for part in parts[1:]:
            value = self._index(value, part)
            if value is None:
                return None
        return value

    def _index(self, container, key):
        key = key.strip()
        bracket = re.match(r"^\[\s*(.*?)\s*\]$", key)
        if bracket:
            key = bracket.group(1)
        if len(key) > 1 and key[0] == key[-1] and key[0] in "\"'":
            key = key[1:-1]

        if isinstance(container, dict):
            # Dict keys win, so a real `forloop.last` is not shadowed by the
            # list-property shortcut below.
            if key in container:
                return container[key]
            if key in ("size", "first", "last"):
                items = to_liquid_list(container)
                if key == "size":
                    return len(items)
                if key == "first":
                    return items[0] if items else None
                return items[-1] if items else None
            return None

        # Liquid exposes these as properties, not filters: list.size, list.first
        if key in ("size", "first", "last"):
            items = to_liquid_list(container)
            if key == "size":
                return len(items)
            if key == "first":
                return items[0] if items else None
            return items[-1] if items else None
        if isinstance(container, (list, tuple)):
            if re.match(r"^-?\d+$", key):
                position = int(key)
                if -len(container) <= position < len(container):
                    return container[position]
            return None
        if isinstance(container, str) and key.isdigit():
            position = int(key)
            if -len(container) <= position < len(container):
                return container[position]
        return None

    def _eval(self, source, scopes):
        source = source.strip()
        if not source:
            return None
        if source.startswith("(") and source.endswith(")"):
            return self._eval(source[1:-1], scopes)
        if len(source) > 1 and source[0] == source[-1] and source[0] in "\"'":
            return source[1:-1]
        if re.match(r"^-?\d+$", source):
            return int(source)
        if re.match(r"^-?\d*\.\d+$", source):
            return float(source)
        if source == "true":
            return True
        if source == "false":
            return False
        if source in ("nil", "null", "empty", "blank"):
            return None
        return self._lookup(source, scopes)

    def _condition(self, source, scopes):
        if not source:
            return False
        for joiner, combine in ((" or ", any), (" and ", all)):
            if find_top_level(source, joiner) != -1:
                return combine(
                    self._condition(part, scopes)
                    for part in split_top_level(source, joiner)
                )
        return self._comparison(source, scopes)

    def _comparison(self, source, scopes):
        source = source.strip()

        if source.startswith("not "):
            return not self._condition(source[4:], scopes)

        for operator in ("==", "!=", ">=", "<=", ">", "<"):
            position = find_top_level(source, operator)
            if position == -1:
                continue
            left = self._eval(source[:position], scopes)
            right = self._eval(source[position + len(operator):], scopes)
            return self._apply_operator(operator, left, right, source[position + len(operator):], scopes)

        if find_top_level(source, " contains ") != -1:
            left_source, _, right_source = source.partition(" contains ")
            left = self._eval(left_source, scopes)
            right = self._eval(right_source, scopes)
            if isinstance(left, (list, tuple)):
                return any(self._stringify(i) == self._stringify(right) for i in left)
            return self._stringify(right) in self._stringify(left)

        return is_truthy(self._eval(source, scopes))

    def _apply_operator(self, operator, left, right, right_source, scopes):
        if operator == "==":
            return self._values_equal(left, right, right_source, scopes)
        if operator == "!=":
            return not self._values_equal(left, right, right_source, scopes)

        if isinstance(left, str) or isinstance(right, str):
            return False
        left_number = self._number(left)
        right_number = self._number(right)
        if operator == ">":
            return left_number > right_number
        if operator == "<":
            return left_number < right_number
        if operator == ">=":
            return left_number >= right_number
        return left_number <= right_number

    def _values_equal(self, left, right, right_source, scopes):
        if right_source.strip() in ("true", "false"):
            if left is None:
                return right_source.strip() == "false"
            return left is (right_source.strip() == "true")
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            return [self._stringify(v) for v in left] == [self._stringify(v) for v in right]
        if isinstance(left, bool) or isinstance(right, bool):
            return bool(left) == bool(right)
        if left is None or right is None:
            return self._stringify(left) == self._stringify(right)
        return self._stringify(left) == self._stringify(right)

    # -- jekyll filters on collections --------------------------------
    def apply_where_exp(self, items, item_name, expression, scopes):
        kept = []
        for item in items:
            scope = [dict(scopes[0])]
            scope[0][item_name] = item
            if self._condition(expression, scope):
                kept.append(item)
        return kept


def render_layout(workspace, layout_name, context, content=""):
    """Render _layouts/<name>.html with a pre-built context."""
    path = os.path.join(workspace, "_layouts", layout_name + ".html")
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()

    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", source, re.DOTALL)
    if match:
        source = match.group(2)

    full = dict(context)
    full["content"] = content
    renderer = LiquidRenderer(workspace)
    output = renderer.render(source, [full])
    return output, renderer.unsupported
