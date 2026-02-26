# Interactive Visual Exploration of Dual Encoder Attributions

This repository contains a tool for visualizing attributions from Dual Encoders for text-text pairs and text-image pairs.
This variant uses live-computed attribution data via an external API. It is a work in progress, intended to showcase the potential of computing inputs on the fly. Providing such an API is outside the scope of this project.
An extensive description of the project can be found in the accompanying paper (coming soon).

## Quickstart

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
