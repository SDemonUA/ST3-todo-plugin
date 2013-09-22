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

class ShowTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        s = sublime.load_settings('Todo.sublime-settings')
        todo_selectors = []
        self.todos = []
        todos = []
        ts = []

        for regex in s.get('todo_string_prefix', ["^TODO"]):
            todo_selectors.append(re.compile(regex))

        # Split comments into lines
        v = self.view
        for r in v.find_by_selector('comment'):
            todos += v.lines(r) # list + list

        # Filter comments by TODO selector
        for r in todos:
            comment_prefixes = get_comment_prefixes(v, r.begin())
            s = v.substr(r).strip()
            for pref in comment_prefixes:
                if s.find(pref, 0) is not -1:
                    s = s[len(pref):len(s)].lstrip()
                    for regex in todo_selectors:
                        if regex.match(s):
                            if len (s) > 65 :
                                s = s[:62]+'...'
                            ts.append(s)
                            self.todos.append(r)
                            break
                    break

        # Show panel with TODOs
        if len(ts) > 0:
            # TODO: Save some sings of quick panel presense
            self.old_vis_vector=v.viewport_position()
            v.window().show_quick_panel(ts, self.on_done, sublime.MONOSPACE_FONT, 0, self.on_hl_panel_item)
            # v = self.window.get_output_panel('todo_list')

            # edit = v.begin_edit()
            # v.insert(edit, 0, u"\n".join(line for line in ts))
            # v.end_edit(edit)

            # self.window.run_command("show_panel", {"panel": "output.todo_list"})
        else:
            sublime.status_message("No TODOs in this file.")
        return

    def on_done(self, idx):
        if idx is not -1:
            self.view.sel().clear()
            self.view.sel().add(self.todos[idx])
            self.view.show(self.todos[idx])
        else:
            self.view.set_viewport_position(self.old_vis_vector)

        return

    def on_hl_panel_item(self, idx):
        if idx is not -1:
            self.view.show(self.todos[idx])
        return

    def is_visible(args):
        return True

    def description(args):
        return "List TODOs in openned file."

# TODO: detect focus changes in quick_panel