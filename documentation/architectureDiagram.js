graph TD
    %% User
    User[Research User]

    %% System
    GUI[GUI]
    Backend[Backend System<br/>Import, Calculate, Classify, Visualize, Export]

    %% Data
    Input[(Input Files<br/>.xlsx, .csv, .txt)]
    Output[(Output<br/>Plots & Results)]
        TESTING

    %% Flow
    User --- |Interact| GUI
    GUI --- |Command| Backend
    Backend --- |Feedback| GUI
    Input --- |Read| Backend
    Backend --- |Write| Output