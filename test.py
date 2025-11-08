import requests
import time

input_recipe = {
    "recipe_text": """# Nigerian Jollof Rice

This is the party rice of West Africa - smoky, spicy, and absolutely irresistible. Every cook has their own method, but this version focuses on building deep flavor through proper technique. The key is patience with the tomato base and not disturbing the rice too much once it's cooking.

## Ingredients

- 3 cups long-grain parboiled rice
- 4 cups chicken stock
- 1 cup water
- 400g canned tomatoes (or 6 fresh Roma tomatoes)
- 2 red bell peppers
- 1 scotch bonnet pepper
- 2 medium onions
- 3 cloves garlic
- 1 inch fresh ginger
- 1/4 cup vegetable oil
- 3 tbsp tomato paste
- 2 bay leaves
- 1 tsp curry powder
- 1 tsp dried thyme
- 1 tsp smoked paprika
- 2 chicken bouillon cubes
- Salt and pepper to taste

## Instructions

Start by making your pepper and tomato blend. Roughly chop your tomatoes, red bell peppers, scotch bonnet pepper, one whole onion, garlic, and ginger. Throw everything into a blender and blend until completely smooth - you want no chunks. This blend is what gives Jollof its signature flavor so don't skip this step.

Next, rinse your rice really well under cold running water, swishing it around with your hands until the water runs completely clear. This removes excess starch and helps keep the grains separate. Drain it thoroughly and set it aside in a bowl.

Now we build the base. Heat your oil in a large heavy pot - and I mean heavy, like a Dutch oven or a thick-bottomed pot. You don't want anything flimsy here. Get it nice and hot over medium heat. Dice up your second onion and toss it in, stirring it around for about 2-3 minutes until it softens and starts to smell sweet.

Add your tomato paste and this is important - fry it. Keep stirring constantly for about 2 minutes. You'll see it darken slightly. This removes the raw taste and adds depth.

Pour in your blended tomato mixture and now comes the patience part. You need to let this cook down for 15-20 minutes on medium-high heat, stirring every few minutes. You'll know it's ready when the sauce has reduced significantly, darkened in color, and the oil starts to separate and float on top. Some people call this "frying out the tomatoes" - it's crucial for authentic Jollof.

When your base is ready, add all your spices - curry powder, thyme, smoked paprika, bay leaves, and crumble in those bouillon cubes. Stir everything together and let it cook for 2 minutes to bloom the spices and wake up their flavors.

Pour in your chicken stock and water, stir well, and bring it all to a rolling boil. Taste it now and adjust your salt and pepper - this is your chance to get the seasoning right because you won't be stirring much after this.

Add your drained rice and give it one good stir to make sure every grain is coated in that beautiful red sauce. Spread it out evenly in the pot. Let it cook uncovered on medium-high heat, without stirring, until the liquid has reduced to just about level with the rice. You should see little holes forming in the surface - these are steam vents.

Now turn your heat down to the absolute lowest setting. Take a piece of aluminum foil and cover the pot tightly, then put the lid on top of the foil. This creates a seal that traps steam. Let it cook undisturbed for 30-40 minutes. I know it's tempting but don't lift that lid!

After the time is up, turn off the heat and let it rest for 5 minutes still covered. Then remove the lid and foil, and gently fluff the rice with a fork from the edges toward the center. Some people fight over the crispy bottom layer - if you like that, just scrape it up and mix it through.

Serve it hot with fried plantains, coleslaw, or your protein of choice.

**Serves 6-8 | Cook time: About 90 minutes**"""
}

start_time = time.time()
response = requests.post("http://localhost:8000/v1/techinque-extract", json=input_recipe)
print(response.json())

print(f"\n\nFinished in {time.time() - start_time} seconds")