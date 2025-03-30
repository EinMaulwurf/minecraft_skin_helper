import argparse
import os
from PIL import Image
from typing import Tuple

# For checking image size. Should be either 64x32 (Java lagacy), 64x64 (Java) or 128x128 (Bedrock)
valid_sizes = [(64, 32), (64, 64), (128, 128)]


def rgba_to_hex(rgba: Tuple[int, int, int, int]) -> str:
    """Converts an RGBA tuple (0-255) to an #RRGGBBAA hex string."""
    r, g, b, a = rgba
    return f"#{r:02X}{g:02X}{b:02X}{a:02X}"


def hex_to_rgba(hex_code) -> Tuple[int, int, int, int]:
    """Converts an #RRGGBBAA hex string to an RGBA tuple (0-255)."""
    if not hex_code.startswith("#") or len(hex_code) != 9:
        raise ValueError(f"Invalid hex code format: {hex_code}. Expected #RRGGBBAA")
    try:
        r = int(hex_code[1:3], 16)
        g = int(hex_code[3:5], 16)
        b = int(hex_code[5:7], 16)
        a = int(hex_code[7:9], 16)
        return (r, g, b, a)
    except ValueError:
        raise ValueError(f"Invalid characters in hex code: {hex_code}")


def png_to_hex_grid(input_png_path: str, output_txt_path: str) -> None:
    """
    Reads a PNG image and writes its pixel colors as a grid of hex codes
    (#RRGGBBAA) to a text file.
    """
    if not os.path.exists(input_png_path):
        print(f"Error: Input PNG file not found: {input_png_path}")
        return

    try:
        img = Image.open(input_png_path)
        # Ensure image is in RGBA format to handle transparency consistently
        img = img.convert("RGBA")
        width, height = img.size

        if img.size not in valid_sizes:
            raise ValueError(
                f"Image has wrong dimension. Should be one of 64x32 (Java legacy), 64x64 (Java) or 128x128 (Bedrock). Yours is {width}x{height}."
            )

        pixels = img.load()

        print(f"Image loaded: {input_png_path} ({width}x{height})")

        with open(output_txt_path, "w") as f:
            for y in range(height):
                row_hex_codes = []
                for x in range(width):
                    rgba = pixels[x, y]
                    hex_code = rgba_to_hex(rgba)
                    row_hex_codes.append(hex_code)
                # Write row with spaces separating hex codes
                f.write(" ".join(row_hex_codes) + "\n")

        print(f"Hex grid successfully written to: {output_txt_path}")

    except FileNotFoundError:
        print(f"Error: Could not find the input file: {input_png_path}")
    except Exception as e:
        print(f"An error occurred during PNG to Text conversion: {e}")


def hex_grid_to_png(input_txt_path: str, output_png_path: str) -> None:
    """
    Reads a text file containing a grid of hex codes (#RRGGBBAA) and
    creates a PNG image from it.
    """
    if not os.path.exists(input_txt_path):
        print(f"Error: Input text file not found: {input_txt_path}")
        return

    try:
        with open(input_txt_path, "r") as f:
            lines = f.readlines()

        if not lines:
            print("Error: Input text file is empty.")
            return

        # Clean up lines and split into hex codes
        grid_data = []
        expected_width = -1
        for y, line in enumerate(lines):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            row_hex_codes = line.split()
            if expected_width == -1:
                expected_width = len(row_hex_codes)
            elif len(row_hex_codes) != expected_width:
                raise ValueError(
                    f"Inconsistent row length found at row {y + 1}. Expected {expected_width}, got {len(row_hex_codes)}."
                )

            grid_data.append(row_hex_codes)

        height = len(grid_data)
        width = expected_width

        if [width, height] not in valid_sizes:
            raise ValueError(
                f"HEX data has wrong dimension. Should be one of 64x32 (Java legacy), 64x64 (Java) or 128x128 (Bedrock). Yours is {width}x{height}."
            )

        print(f"Text grid loaded: {input_txt_path} (Detected size: {width}x{height})")

        # Create a new RGBA image
        img = Image.new("RGBA", (width, height))
        pixels = img.load()

        # Populate the image with pixels from hex codes
        for y in range(height):
            for x in range(width):
                try:
                    hex_code = grid_data[y][x]
                    rgba = hex_to_rgba(hex_code)
                    pixels[x, y] = rgba
                except IndexError:
                    # This shouldn't happen with the earlier width check, but as a safeguard
                    print(
                        f"Error: Index out of bounds at ({x},{y}). Check grid consistency."
                    )
                    # Fill with a default color like transparent black
                    pixels[x, y] = (0, 0, 0, 0)
                except ValueError as ve:
                    print(
                        f"Error parsing hex code at row {y + 1}, column {x + 1}: {ve}. Using transparent black."
                    )
                    pixels[x, y] = (0, 0, 0, 0)  # Default to transparent black on error

        img.save(output_png_path, "PNG")
        print(f"PNG image successfully created at: {output_png_path}")

    except FileNotFoundError:
        print(f"Error: Could not find the input file: {input_txt_path}")
    except ValueError as ve:
        print(f"An error occurred processing the text grid: {ve}")
    except Exception as e:
        print(f"An error occurred during Text to PNG conversion: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Minecraft skin PNGs to/from hex code text grids."
    )
    parser.add_argument(
        "mode",
        choices=["png2txt", "txt2png"],
        help="Conversion mode: png to text or text to png.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input file path (PNG for png2txt, TXT for txt2png).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path (TXT for png2txt, PNG for txt2png).",
    )

    args = parser.parse_args()

    if args.mode == "png2txt":
        png_to_hex_grid(args.input, args.output)
    elif args.mode == "txt2png":
        hex_grid_to_png(args.input, args.output)
