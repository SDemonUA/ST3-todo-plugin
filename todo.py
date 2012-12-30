import sublime, sublime_plugin

class ShowTodoCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		todo_selector = 'TODO:'
		self.todos = []
		ts = []

		v = self.view
		todos = []
		# Split comments into lines
		for r in v.find_by_selector('comment'):
			todos += v.lines(r);

		# Filter comments by TODO selector
		for r in todos:
			s = v.substr(r)
			idx = s.find(todo_selector, 0, 10)
			if idx is not -1:
				ts.append(s[idx+len(todo_selector):30].lstrip())
				self.todos.append(r)

		# Show panel with TODOs
		if len(ts) > 0:
			# v = self.window.get_output_panel('todo_list')

			# edit = v.begin_edit()
			# v.insert(edit, 0, u"\n".join(line for line in ts))
			# v.end_edit(edit)

			# self.window.run_command("show_panel", {"panel": "output.todo_list"})
			v.window().show_quick_panel(ts, self.on_done)
		else:
			sublime.status_message("No TODOs in this file.")
		return

	def on_done(self, idx):
		if idx is not -1:
			self.view.show(self.todos[idx])
		return

	def is_visible(args):
		return True

	def description():
		return "See TODOs in openned file."
