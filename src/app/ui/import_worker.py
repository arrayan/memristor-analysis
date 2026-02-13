from PySide6.QtCore import QObject, Signal, Slot
# Replace 'plotting_module' with the actual filename/path of your plotting script
from plotting.run import main as run_plotting_pipeline 

class ImportWorker(QObject):
    progress = Signal(int)
    status_message = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, path, mode, converter_class):
        super().__init__()
        self.path = path
        self.mode = mode
        self.converter_class = converter_class

    @Slot()
    def run(self):
        try:
            # --- STEP 1: Data Conversion (Importing to DuckDB) ---
            self.status_message.emit("Phase 1/2: Updating database from raw files...")
            self.progress.emit(10)
            
            converter = self.converter_class("output.duckdb")
            converter.convert(self.path)
            
            self.progress.emit(50)

            # --- STEP 2: Plotting (Generating HTMLs) ---
            self.status_message.emit("Phase 2/2: Generating HTML plots (this may take a moment)...")
            
            # This calls the 'main()' function from your plotting script exactly as it is.
            # It will load the config, read the DB, and write the files.
            run_plotting_pipeline()

            self.progress.emit(100)
            self.finished.emit()
            
        except Exception as e:
            # If anything fails in the converter OR the plotting script, catch it here
            self.error.emit(str(e))