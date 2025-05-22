#!/bin/bash

file="$1"

echo "PostProcessing ongoing"

sed -i "s/\$ref: '\#\/components\/schemas\/Uint16'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/UInt16'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/Uint8'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/UInt8'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/Integer'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/String'/type: string/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/string'/type: string/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/Bool'/type: boolean/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/bool'/type: boolean/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/16bits bitmap'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/UnsignedInt'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/UInt128'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/Uint128'/type: integer/g" $file
sed -i "s/\$ref: '\#\/components\/schemas\/URI'/type: string/g" $file

# replace with proper indentation
# sed -i "s/                \$ref: '\#\/components\/schemas\/Uint32'/                type: integer\\n                format: uint32/g" $file
# sed -i "s/          \$ref: '\#\/components\/schemas\/Uint32'/          type: integer\\n          format: uint32/g" $file
# sed -i "s/                \$ref: '\#\/components\/schemas\/UInt32'/                type: integer\\n                format: uint32/g" $file
# sed -i "s/          \$ref: '\#\/components\/schemas\/UInt32'/          type: integer\\n          format: uint32/g" $file
sed -i "s/                \$ref: '\#\/components\/schemas\/Uint64'/                type: integer\\n                format: int64/g" $file
sed -i "s/          \$ref: '\#\/components\/schemas\/Uint64'/          type: integer\\n          format: int64/g" $file
sed -i "s/                \$ref: '\#\/components\/schemas\/UInt64'/                type: integer\\n                format: int64/g" $file
sed -i "s/          \$ref: '\#\/components\/schemas\/UInt64'/          type: integer\\n          format: int64/g" $file
sed -i "s/                \$ref: '\#\/components\/schemas\/Float'/                 type: number\\n                 format: float/g" $file
sed -i "s/          \$ref: '\#\/components\/schemas\/Float'/           type: number\\n          format: float/g" $file

sed -i "s/'# /# /g" $file

echo "PostProcessing done"
