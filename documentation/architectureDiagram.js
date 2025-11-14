graph TD
    %% User
    User[Research User]

    %% System
    GUI[GUI]
    Backend[Backend System<br/>Import, Calculate, Classify, Visualize, Export]

    %% Data
    Input[(Input Files<br/>.xlsx, .csv, .txt)]
    Output[(Output<br/>Plots & Results)]

    %% Flow
    User -->|Interacts| GUI
    GUI -->|Commands| Backend
    Backend -->|Feedback| GUI
    Input -->|Read| Backend
    Backend -->|Write| Output