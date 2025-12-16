from database.supabase_client import create_run, finish_run

class RunManager:
    """
    Class that manages the lifecycle of a benchmark run.
    Wrapper simple for create_run() and finish_run().
    """
    
    def __init__(self, run_name="auto-run", triggered_by="system"):
        """
        Initialize RunManager.
        
        Args:
            run_name: Name of the run (e.g. "mvp-validation-run")
            triggered_by: Who triggered the run (e.g. "system", "user")
        """
        self.run_name = run_name
        self.triggered_by = triggered_by
        self.run_id = None  # set to None until start() is called

    def start(self):
        """
        Fill a new run in db and get the UUID of the created run.

        Returns:
            UUID of the created run
        """
        # Create run in db and get the UUID of the created run
        self.run_id = create_run(self.run_name, self.triggered_by)
        print(f"Run started: {self.run_id}")

    def end(self):
        """
        End the run by setting the finished_at timestamp.
        """
        # Update the run by setting the finished_at timestamp to the current timestamp
        finish_run(self.run_id)
        print(f"Run finished: {self.run_id}")
