# Interactive Visual Exploration of Dual Encoder Attributions

This repository contains a tool for visualizing attributions from Dual Encoders for text-text pairs and text-image pairs. In this Version, the features are demonstrated with precomputed attribution scores in `.pkl` files.
An extensive description of the project can be found in the accompanying paper (coming soon).

## Quickstart

##### Using the prebuilt package from the Release:

Download the `.zip` file from the latest release and execute the `run.bat` or `run.sh` script.

##### Using docker:

Execute in root directory

```
docker compose up
```

##### Running manually:

```
cd app
python -m uvicorn app:app --host 0.0.0.0 --port 8020
```

```
cd attribution_visualization
npm install
npm run dev
```
