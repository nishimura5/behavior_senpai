class DfAttrs:
    def __init__(self, src_df):
        self.attrs = src_df.attrs

    def load_proc_history(self):
        if "proc_history" not in self.attrs.keys():
            print("proc_history not found.")
            return
        if isinstance(self.attrs["proc_history"], list) is False:
            print("proc_history is not list.")
            return
        proc_history_list = []
        for history in self.attrs["proc_history"]:
            if isinstance(history, dict) and "proc" in history.keys() and "source_cols" in history.keys():
                proc_history_list.append(history)
            else:
                print("invalid proc_history.")
        self.newest_proc_history = proc_history_list[-1]

    def chk_model(self, model_name):
        if self.sttrs["model"] != model_name:
            print(f"model_name({model_name}) unmatch.")
            return False
        return True

    def chk_newest_history_proc(self, proc_name):
        if self.newest_proc_history["proc"] != proc_name:
            print(f"proc_name({proc_name}) unmatch.")
            return False
        if len(self.newest_proc_history["source_cols"]) == 0:
            print("source_cols is empty.")
            return False
        return True

    def get_source_cols(self):
        return self.newest_proc_history["source_cols"]

    def append_history_proc(self, proc_name, source_cols):
        if "proc_history" not in self.attrs.keys():
            self.attrs["proc_history"] = []
        self.attrs["proc_history"].append({"proc": proc_name, "source_cols": source_cols})
