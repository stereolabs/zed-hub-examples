## Multiplatform deployment

This sample shows how to deploy a multiplatform application.

## File structure
The difference with other samples is that there are multiple `docker-compose*.yml` files. Your devices will automatically use the one it needs according to its naming. You don't need all of them. The main `docker-compose.yml` file is still there, it's used as a fallback if the right one is not found.

## Building source
Different platforms will need different binaries. To achieve that, this sample let the device building the binaries. This building step is in the beginning of the `Dockerfile`. If you prefer, you can also build your images before, push them in a registry, fill the `docker-compose*.yml` files with the right image names, and your devices won't need to build from the source anymore. 

## Deployment
To deploy, run 
```
cd ./cpp
edge_cli deploy .
```
Or you can build the .zip file yourself, containing :
- the `app` folder and everything inside it
- `app.json`
- all `docker-compose-*.yml` files