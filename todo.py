import sublime, sublime_plugin, re

def get_comment_prefixes(view, pt):
    shell_vars = view.meta_info("shellVariables", pt)
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

def get_todo_regions(view, selectors):
    lines = []
    todos = []
    # Split comments into lines
    for r in view.find_by_selector('comment'):
        lines += view.lines(r)

    # Filter comments by TODO selector
    for r in lines:
        comment_prefixes = get_comment_prefixes(view, r.begin())
        s = view.substr(r).strip()
        for pref in comment_prefixes:
            if s.find(pref, 0) is not -1:
                s = s[len(pref):len(s)].lstrip()
                for regex in selectors:
                    if regex.match(s):
                        if len (s) > 65 :
                            s = s[:62]+'...'
                        todos.append({"title" : s, "region" : r})
                        break
                break
    return todos

def get_todo_selectors():
    todo_selectors = []
    s = sublime.load_settings('Todo.sublime-settings')
    for regex in s.get('todo_string_prefix', ["^TODO"]):
        todo_selectors.append(re.compile(regex))

    return todo_selectors

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

            todos = get_todo_regions(view, get_todo_selectors())
            self.view.insert(edit, 0, u"\n".join(line["title"] + " [ line " + str(view.rowcol(line["region"].begin())[0]+1) + " ]" for line in todos))
            
        return


    def is_visible(args):
        # TODO detect if we are in search result view
        return True

    def description(args):
        return "List TODOs in this file."


class ShowTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = sublime.load_settings('Todo.sublime-settings')
        view = self.view
        self.todos = get_todo_regions(view, get_todo_selectors())   

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
            view.window().show_quick_panel(todo_titles, self.on_done, sublime.MONOSPACE_FONT, 0, self.on_hl_panel_item)
        else:
            sublime.status_message("No TODOs in this file.")
        return

    def on_done(self, idx):
        if idx is not -1:
            self.view.sel().clear()
            self.view.sel().add(self.todos[idx]["region"])
            self.view.show_at_center(self.todos[idx]["region"])
        else:
            self.view.set_viewport_position(self.old_vis_vector)

        return

    def on_hl_panel_item(self, idx):
        if idx is not -1:
            self.view.show_at_center(self.todos[idx]["region"])
        return

    def is_visible(args):
        # TODO detect if we are in search result view
        return True

    def description(args):
        return "List TODOs in this file."

# TODO: detect focus changes in quick_panel