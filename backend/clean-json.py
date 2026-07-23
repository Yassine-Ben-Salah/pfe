import json
import re

INPUT_FILE = r"D:\projects\extraction\constat_output.json"
OUTPUT_FILE = "cleaned.json"   # 👈 output file


def extract_from_markdown(markdown):
    text = markdown.lower().replace("**", "")

    type_match = re.search(r"marque, type\s*:\s*(.+)", text)
    damage_match = re.search(r"dégâts apparents \(a\)\s*:\s*(.+)", text)

    car_type = type_match.group(1).strip() if type_match else None
    damage = damage_match.group(1).strip() if damage_match else None

    if car_type:
        parts = car_type.split("-")
        marque = parts[0].strip()
        type_veh = parts[-1].strip()
    else:
        marque, type_veh = None, None

    if damage:
        damage = (
            damage.replace("/", " ")
                  .replace("-", " ")
                  .strip()
        )

    return {
        "marque": marque,
        "type": type_veh,
        "damage_text": damage
    }


def main():

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for page in data.get("pages", []):
        md = page.get("markdown", "")
        extracted = extract_from_markdown(md)
        results.append(extracted)

    # ✅ SAVE TO FILE
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved to {OUTPUT_FILE}")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()