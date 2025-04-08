from PIL import Image

def place_logo(apparel_path, logo_path, output_path, position, scale=0.2):
    #load apparel image
    apparel = Image.open(apparel_path).convert("RGBA")
    
    #load and resize logo based on apparel image
    #scale = 0.n  # n0% of the apparel width
    logo = Image.open(logo_path).convert("RGBA")
    logo = logo.resize((int(apparel.width * scale), int(logo.height * apparel.width * scale / logo.width)))

    #calc position
    if position == "center":
        x = (apparel.width - logo.width) // 2
        y = (apparel.height - logo.height) // 2
    elif position == "top_left":
        x, y = 50, 50  #tweak
    else:
        x, y = position  #custom tuple position input

    #Composite
    apparel.paste(logo, (x, y), logo)

    #Save result
    apparel.save(output_path, format="PNG")

#Example usage
place_logo("tshirt.png", "logo.png", "output.png", position="center")