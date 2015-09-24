import sublime, sublime_plugin, re

def get_comment_prefixes(view, pt):
    shell_vars = view.meta_info("shellVariables", pt) # view.meta_info(key, point)
    if not shell_vars:
        return []

    # transform the list of dicts into a single dict
    all_vars = {}
    for v in shell_vars:
        if 'name' in v and 'value' in v:
            all_vars[v['name']] = v['value']

    prefixes = []

    # transform the dict into a single array of valid comments
    suffixes = [""] + ["_" + str(i) for i in range(1, 10)]
    for suffix in suffixes:
        start = all_vars.setdefault("TM_COMMENT_START" + suffix)

        if start:
            prefixes.append(start)
            prefixes.append(start.strip())

    return prefixes

def get_todo_regions(view):
    lines = []
    todos = []
    selectors = []

    # Get selectors from user settings
    stng = sublime.load_settings('Todo.sublime-settings')
    for regex in stng.get('todo_string_prefix', ["^TODO"]):
        selectors.append(re.compile(regex))

    # Split comments into lines
    for r in view.find_by_selector('comment'):
        lines += view.lines(r)

    # Filter comments by TODO selector
    for r in lines:
        comment_prefixes = get_comment_prefixes(view, r.begin())
        s = view.substr(r).strip()
        for pref in comment_prefixes:
            cpos = s.find(pref, 0)
            if cpos is not -1:
                s = s[cpos+len(pref):len(s)].lstrip()
                for regex in selectors:
                    if regex.match(s):
                        if len (s) > 65 :
                            s = s[:62]+'...'
                        todos.append({"title" : s, "region" : r})
                        break
                break
    return todos

def no_todos_found():
    sublime.status_message("No TODOs in this file.")
    return

class ListTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit, view_id=False):
        if not view_id:
            window = self.view.window()
            v = window.create_output_panel('todo_list')
            window.run_command("show_panel", {"panel" : "output.todo_list"})
            v.run_command("list_todo", {"view_id" : self.view.id()})
        else:
            view = False
            for v in self.view.window().views():
                if v.id() is view_id:
                    view = v;

            if not view:
                return

            todos = get_todo_regions(view)
            if len(todos) is 0:
                no_todos_found()
            else:
                self.view.insert(edit, 0, u"\n".join(line["title"] + " [ line " + str(view.rowcol(line["region"].begin())[0]+1) + " ]" for line in todos))

        return


    def is_visible(args):
        # TODO detect if we are in search result view
        return True

    def description(args):
        return "List TODOs in this file."


class ShowTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        self.todos = get_todo_regions(view)

        # Show panel with TODOs
        if len(self.todos) > 0:
            todo_titles = []
            for td in self.todos:
                if "title" in td:
                    todo_titles.append(td["title"])
                else:
                    todo_titles.append("<empty>")

            # TODO: Save some sings of quick panel presense
            self.old_vis_vector = view.viewport_position()
            self.prev_hl_idx = -1
            view.window().show_quick_panel(todo_titles, self.on_done, sublime.MONOSPACE_FONT, 0, self.on_hl_panel_item)
        else:
            no_todos_found()
        return

    def on_done(self, idx):
        if idx is not -1:
            self.view.sel().clear()
            self.view.sel().add(self.todos[idx]["region"])
            self.view.show_at_center(self.todos[idx]["region"])
        else:
            for todo in self.todos:
                self.view.sel().subtract(todo["region"])
            self.view.set_viewport_position(self.old_vis_vector)

        return

    def on_hl_panel_item(self, idx):
        if self.prev_hl_idx is not -1:
            self.view.sel().subtract(self.todos[self.prev_hl_idx]["region"])

        if idx is not -1:
            region = self.todos[idx]["region"]
            self.view.sel().add(region)
            self.view.show_at_center(region)
            self.prev_hl_idx = idx
        return

    def is_visible(args):
        return True # TODO detect if we are in search result view

    def description(args):
        return "List TODOs in this file."


# TODO erase self.todos on any input ?
class CarouselTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit, reverse=False):
        view = self.view;
        self.todos = get_todo_regions(view)

        if len(self.todos) is 0:
            no_todos_found()
            return

        if not reverse:
            if not hasattr(self, "last_idx"):
                self.last_idx = -1
            self.last_idx = (self.last_idx+1) % len(self.todos)
        else:
            if not hasattr(self, "last_idx"):
                self.last_idx = len(self.todos)
            self.last_idx = (self.last_idx-1) % len(self.todos)

        view.show_at_center(self.todos[self.last_idx]["region"])
        view.sel().clear()
        view.sel().add(self.todos[self.last_idx]["region"])

        return
    def is_visible(args):
        return True
    def description(args):
        return "Cycle trought TODOs in this file."

# TODO: detect focus changes in quick_panel

class AddTodoCommand(sublime_plugin.TextCommand):
    """Add new TODO in relative to cursor position AddTodoCommand"""
    def run(self, edit):
        view = self.view

        # Detect what caracters used for comments in this "scope"
        region_prefix_set = []
        for region in view.sel():
            prefixes = get_comment_prefixes(view, region.end())
            if len (prefixes) is not 0:
                region_prefix_set.append([region, prefixes])

        # Compose TODO content - some sort of snippet or even use snippet to do this
        snippet = "TODO: text? [by ME]" # TODO change this

        sel = view.sel()
        sel.clear()
        for region_prefix in region_prefix_set:
            if view.classify(region_prefix[0].end()) & (sublime.CLASS_LINE_END | sublime.CLASS_EMPTY_LINE):
                sel.add(region_prefix[0].end())
                view.insert(edit, region_prefix[0].end(), region_prefix[1][0] + snippet)
            else:
                sel.add(view.line(region_prefix[0].end()).end())
                view.insert(edit, view.line(region_prefix[0].end()).end(), " " + region_prefix[1][0] + snippet)

        return
    def is_visible(self):
        # Detect if view is writable
        if self.view.is_read_only():
            return False

        # Detect if regions has known comment prefixes
        regions = len (self.view.sel())
        unavail = 0
        for region in self.view.sel():
            if len (get_comment_prefixes(self.view, region.begin())) is 0:
                unavail = unavail + 1

        if unavail is regions:
            return False

        return True
    def description(args):
        return "Add new TODO"
