from dataclasses import dataclass, field
from typing import List


@dataclass
class Variable:
    name: str
    type: str = "int"
    value: int = 1

    def to_dict(self):
        return {"name": self.name, "type": self.type, "value": self.value}

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], type=d.get("type", "int"), value=d.get("value", 1))


@dataclass
class SumExpression:
    operands: List[str]

    def to_dict(self):
        return {"operands": self.operands}

    @classmethod
    def from_dict(cls, d):
        return cls(operands=d["operands"])


@dataclass
class ProgramIR:
    language: str = "c"
    includes: List[str] = field(default_factory=lambda: ["stdio.h"])
    variables: List[Variable] = field(default_factory=list)
    expression: SumExpression = field(default_factory=lambda: SumExpression([]))
    print: bool = True
    return_code: int = 0

    def to_dict(self):
        return {
            "language": self.language,
            "includes": self.includes,
            "variables": [v.to_dict() for v in self.variables],
            "expression": self.expression.to_dict(),
            "print": self.print,
            "return_code": self.return_code,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            language=d.get("language", "c"),
            includes=d.get("includes", ["stdio.h"]),
            variables=[Variable.from_dict(v) for v in d.get("variables", [])],
            expression=SumExpression.from_dict(d.get("expression", {"operands": []})),
            print=d.get("print", True),
            return_code=d.get("return_code", 0),
        )
