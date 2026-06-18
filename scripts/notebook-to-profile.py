import argparse
import asyncio
import io

from fastapi import UploadFile

import app.routers.profile_router

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--notebook", type=argparse.FileType("rb"), required=True)
    args = parser.parse_args()

    notebook_file = UploadFile(filename=args.notebook.name, file=io.BytesIO(args.notebook.read()))

    profile = asyncio.run(app.routers.profile_router.profile_notebook(
        notebook_file=notebook_file,
        taxonomy_name=app.routers.profile_router.TaxonomyFunction.DSPIPELINES,
        profiler_name=app.routers.profile_router.ProfilerFunction.EMBEDDING,
        parser_name=app.routers.profile_router.ParserFunction.DSPIPELINES,
    ))
