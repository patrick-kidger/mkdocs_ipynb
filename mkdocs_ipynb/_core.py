import base64
import json
import pathlib
import re
import uuid
from typing import Any

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files, InclusionLevel


class _NotebookFile(File):
    def is_documentation_page(self) -> bool:
        return True


_ansi_regex = re.compile(r"\x1b\[[;?0-9]*[a-zA-Z]")


def _source(source: list[str], lang: str, new_content: list[str], newlines: bool):
    content = ("\n" if newlines else "").join(source).strip()
    content = _ansi_regex.sub("", content)
    code_block = "```"
    while code_block in content:
        code_block += "`"
    new_content.append(f"{code_block}{lang}\n")
    new_content.append(content)
    new_content.append(f"\n{code_block}")


def _image_png(data: str, new_content: list[str], aux: dict[str, bytes]) -> None:
    image_filename = uuid.uuid4().hex + ".png"
    aux[image_filename] = base64.b64decode(data)
    new_content.append(f"![img](./_data/{image_filename})")


def _text_plain(data: list[str], new_content: list[str], aux: dict[str, bytes]) -> None:
    del aux
    _source(data, "", new_content, newlines=False)


_supported_mimetypes = {"image/png": _image_png, "text/plain": _text_plain}


def _data(datas: dict[str, Any], new_content: list[str], aux: dict[str, bytes]):
    for mimetype_name, mimetype_converter in _supported_mimetypes.items():
        if mimetype_name in datas:
            mimetype_converter(datas[mimetype_name], new_content, aux)
            return
    available_mimetype_names = list(datas.keys())
    supported_mimetype_names = list(_supported_mimetypes.keys())
    raise ValueError(
        f"No supported mimetype found. Available types are {available_mimetype_names}, "
        f"supported types are {supported_mimetype_names}"
    )


def _ipynb_to_md(file: File) -> tuple[str, dict[str, bytes]]:
    content = json.loads(file.content_string)
    new_content: list[str] = []
    aux: dict[str, bytes] = {}
    for cell in content["cells"]:
        match cell["cell_type"]:
            case "code":
                _source(cell["source"], "python", new_content, newlines=False)
                for output in cell["outputs"]:
                    new_content.append("\n\n")
                    match output["output_type"]:
                        case "stream":
                            _source(output["text"], "", new_content, newlines=False)
                        case "error":
                            _source(
                                output["traceback"],
                                "python",
                                new_content,
                                newlines=True,
                            )
                        case "execute_result":
                            _data(output["data"], new_content, aux)
                        case "display_data":
                            _data(output["data"], new_content, aux)
                        case other:
                            raise ValueError(
                                f'Found cell with `"output_type": {other}`, which is '
                                "not understood."
                            )
            case "markdown":
                new_content.extend(cell["source"])
            case other:
                raise ValueError(
                    "Can only convert cells of type 'code' or 'markdown'. Got "
                    f"'{other}'."
                )
        new_content.append("\n\n")
    data_folder = pathlib.Path(file.src_uri).parent / "_data"
    return "".join(new_content), {
        str(data_folder / name): value for name, value in aux.items()
    }


class NotebookPlugin(BasePlugin):
    config_scheme = ()

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        del self
        for file in list(files):
            if file.src_uri.endswith(".ipynb"):
                new_content, aux_files = _ipynb_to_md(file)
                files.remove(file)
                new_file = _NotebookFile.generated(
                    config,
                    src_uri=file.src_uri,
                    content=new_content,
                    inclusion=InclusionLevel.INCLUDED,
                )
                files.append(new_file)
                for aux_uri, aux_content in aux_files.items():
                    aux_file = File.generated(
                        config,
                        src_uri=aux_uri,
                        content=aux_content,
                        inclusion=InclusionLevel.INCLUDED,
                    )
                    files.append(aux_file)
        return files
