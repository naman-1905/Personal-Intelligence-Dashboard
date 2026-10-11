#!/usr/bin/env python3
"""Merge a batch of sources into infra/mongo-init/sources-catalog.json.

Run once to add the 2026-10 source expansion (gaming, technology, software,
AI/ML, India, cars, F1, entertainment, marvel). Re-running is idempotent:
entries are deduped by `name` and by feed domain against whatever already
exists in the catalog.

Sites with a known native RSS endpoint use it; everything else falls back to
a Google News "site:" search feed (same mechanism as topic feeds), which
works for any indexed site without an RSS feed.

Usage:  python3 infra/mongo-init/add_sources.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

CATALOG_PATH = Path(__file__).parent / "sources-catalog.json"


def gn(domain: str) -> str:
    """Google News site: search feed — robust fallback for sites without RSS."""
    return (
        f"https://news.google.com/rss/search?q=site:{quote_plus(domain)}"
        "&hl=en-US&gl=US&ceid=US:en"
    )


def gn_query(query: str) -> str:
    """Google News feed for an arbitrary query (e.g. a path-specific site)."""
    return (
        f"https://news.google.com/rss/search?q={quote_plus(query)}"
        "&hl=en-US&gl=US&ceid=US:en"
    )


def S(name: str, display: str, category: str, url: str, tier: int = 3):
    return {"name": name, "display_name": display, "category": category,
            "url": url, "trust_tier": tier}


# Domains allowed to appear more than once (multi-feed / multi-subdomain).
# Values are the *normalized* domains produced by domain_of().
MULTI_DOMAINS = {
    "amazon.com",        # aws + machine-learning + ai blogs (aws.amazon.com)
    "microsoft.com",     # azure blog (+ catalog already carries .NET/MSR/Azure-AI)
    "nvidia.com",        # main blog alongside existing developer blog
    "arxiv.org",         # one feed per arXiv category
    "reddit.com",        # one feed per subreddit
    "thehindu.com",      # The Hindu + Frontline
    "indiatimes.com",    # Times of India + Economic Times
    "stanford.edu",      # AI Index + HAI
    "huggingface.co",    # HF blog + Big Science
    "anthropic.com",     # News + Alignment
    "ibm.com",           # Research + Think
}

# Multi-tenant hosting platforms: identity is the subdomain (or, when there is
# no meaningful subdomain, the first path segment), not the platform domain.
PLATFORM_HOSTS = {
    "github.io",
    "substack.com",
    "medium.com",
    "wordpress.com",
    "blogspot.com",
    "tumblr.com",
    "feedburner.com",
    "googleblog.com",
}
GENERIC_SUBDOMAINS = {"www", "feeds"}

NEW: list[dict] = []

# ---------------------------------------------------------------- gaming ----
NEW += [
    S("ign", "IGN", "gaming", "https://www.ign.com/rss", 1),
    S("gamespot", "GameSpot", "gaming", "https://www.gamespot.com/feeds/mashup/rss/news/", 1),
    S("pcgamer", "PC Gamer", "gaming", "https://www.pcgamer.com/feed/", 2),
    S("polygon", "Polygon", "gaming", "https://www.polygon.com/rss/index.xml", 1),
    S("eurogamer", "Eurogamer", "gaming", "https://www.eurogamer.net/feed", 2),
    S("rockpapershotgun", "Rock Paper Shotgun", "gaming", "https://www.rockpapershotgun.com/feed", 2),
    S("gamesradar", "GamesRadar+", "gaming", "https://www.gamesradar.com/rss/", 2),
    S("kotaku", "Kotaku", "gaming", "https://kotaku.com/rss", 1),
    S("videogameschronicle", "Video Games Chronicle", "gaming", "https://www.vgc.com/feed/", 2),
    S("gamesindustry", "GamesIndustry.biz", "gaming", "https://www.gamesindustry.biz/feeds/rss", 2),
    S("destructoid", "Destructoid", "gaming", "https://www.destructoid.com/feed/", 2),
    S("gameinformer", "The Game Informer", "gaming", gn("gameinformer.com"), 3),
    S("pushsquare", "Push Square", "gaming", gn("pushsquare.com"), 3),
    S("nintendolife", "Nintendo Life", "gaming", "https://www.nintendolife.com/feed", 2),
    S("purexbox", "Pure Xbox", "gaming", gn("purexbox.com"), 3),
    S("gematsu", "Gematsu", "gaming", "https://www.gematsu.com/feed", 2),
    S("siliconera", "Siliconera", "gaming", "https://siliconera.com/feed/", 2),
    S("dualshockers", "DualShockers", "gaming", "https://dualshockers.com/feed", 3),
    S("thegamer", "TheGamer", "gaming", "https://www.thegamer.com/rss.xml", 2),
    S("gamerant", "GameRant", "gaming", "https://gamerant.com/feed/", 3),
    S("gamebyte", "GameByte", "gaming", gn("gamebyte.com"), 3),
    S("si-games", "Sports Illustrated: Games", "gaming", gn("videogames.si.com"), 3),
    S("gamingbolt", "GamingBolt", "gaming", "https://gamingbolt.com/feed", 3),
    S("wccftech", "WCCFtech", "gaming", "https://www.wccftech.com/feed", 2),
    S("tech4gamers", "Tech4Gamers", "gaming", gn("tech4gamers.com"), 3),
    S("gamingonlinux", "Gaming on Linux", "gaming", "https://www.gamingonlinux.com/feed", 2),
    S("massivelyop", "Massively OP", "gaming", "https://massivelyop.com/feed", 3),
    S("mmorpg", "MMORPG.com", "gaming", "https://www.mmorpg.com/feed", 3),
    S("mmo-champion", "MMO-Champion", "gaming", gn("mmo-champion.com"), 3),
    S("wowhead", "WoWHead", "gaming", "https://www.wowhead.com/feed", 2),
    S("icy-veins", "Icy Veins", "gaming", "https://icy-veins.com/feed/", 3),
    S("esports-net", "Esports.net", "gaming", gn("esports.net"), 3),
    S("dexerto", "Dexerto", "gaming", gn("dexerto.com"), 3),
    S("esportsinsider", "Esports Insider", "gaming", gn("esportsinsider.com"), 3),
    S("esports-gg", "Esports.gg", "gaming", gn("esports.gg"), 3),
    S("hltv", "HLTV.org", "gaming", gn("hltv.org"), 2),
    S("liquipedia", "Liquipedia", "gaming", gn("liquipedia.net"), 3),
    S("gosugamers", "GosuGamers", "gaming", gn("gosugamers.net"), 3),
    S("vlr", "VLR.gg", "gaming", gn("vlr.gg"), 3),
    S("tracker-gg", "Tracker.gg", "gaming", gn("tracker.gg"), 3),
    S("opgg", "OP.GG", "gaming", gn("op.gg"), 3),
    S("ugg", "U.GG", "gaming", gn("u.gg"), 3),
    S("game8", "Game8", "gaming", gn("game8.co"), 3),
    S("gamewith", "GameWith", "gaming", gn("gamewith.net"), 3),
    S("rpgsite", "RPGSite", "gaming", gn("rpgsite.net"), 3),
    S("jrpg", "JRPG", "gaming", gn("jrpg.jp"), 3),
    S("rpgfan", "RPGFan", "gaming", gn("rpgfan.com"), 3),
    S("nichegamer", "Niche Gamer", "gaming", gn("nichegamer.com"), 3),
    S("hardcoregamer", "HardcoreGamer", "gaming", gn("hardcoregamer.com"), 3),
    S("gamepressure", "GamePressure", "gaming", gn("gamepressure.com"), 3),
    S("gamewatcher", "GameWatcher", "gaming", "https://gamewatcher.com/feed", 3),
    S("strategyinformer", "Strategy Informer", "gaming", "https://strategyinformer.com/feed", 3),
    S("pcgamesn", "PCGamesN", "gaming", "https://www.pcgamesn.com/feed", 2),
    S("pcgameshardware", "PC Games Hardware", "gaming", gn("pcgameshardware.de"), 3),
    S("game-debate", "Game Debate", "gaming", gn("game-debate.com"), 3),
    S("techpowerup", "TechPowerUp", "technology", "https://www.techpowerup.com/rss.xml", 2),
    S("tomshardware", "Tom's Hardware", "technology", "https://www.tomshardware.com/feeds/all", 1),
    S("digitalfoundry", "Digital Foundry", "gaming", "https://www.digitalfoundry.net/feed", 2),
    S("theloadout", "The Loadout", "gaming", gn("theloadout.com"), 3),
    S("ggrecon", "GGRecon", "gaming", "https://ggrecon.com/feed", 3),
    S("charlieintel", "Charlie Intel", "gaming", "https://charlieintel.com/feed", 3),
    S("insider-gaming", "Insider Gaming", "gaming", "https://insider-gaming.com/feed", 3),
    S("mp1st", "MP1st", "gaming", gn("mp1st.com"), 3),
    S("playstationlifestyle", "PlayStation Lifestyle", "gaming", "https://www.playstationlifestyle.net/feed/", 3),
    S("playstation-blog", "PlayStation Blog", "gaming", "https://playstation.blog/feed", 2),
    S("xbox-news", "Xbox Wire", "gaming", "https://news.xbox.com/en-US/rss/", 2),
    S("nintendo-newsroom", "Nintendo Newsroom", "gaming", gn("news.nintendo.com"), 2),
    S("nintendoeverything", "Nintendo Everything", "gaming", "https://nintendoeverything.com/feed", 3),
    S("mynintendonews", "My Nintendo News", "gaming", "https://www.mynintendonews.com/feed/", 3),
    S("nintendoworldreport", "Nintendo World Report", "gaming", "https://nintendoworldreport.com/feed", 2),
    S("gamexplain", "GameXplain", "gaming", gn("gamexplain.com"), 3),
    S("easyallies", "Easy Allies News", "gaming", gn("easyallies.com"), 3),
    S("gamedeveloper", "Games Developer", "gaming", gn("gamedeveloper.com"), 3),
    S("gamasutra", "Gamasutra (GDC)", "gaming", gn("gamasutra.com"), 3),
    S("gameindustry-eu", "Game Industry EU", "gaming", gn("gameindustry.eu"), 3),
    S("gameworldobserver", "Game World Observer", "gaming", "https://gameworldobserver.com/feed", 3),
    S("pocketgamer", "Pocket Gamer", "gaming", gn("pocketgamer.com"), 3),
    S("app2top", "App2Top", "gaming", "https://app2top.com/feed", 3),
    S("mobilegamer-biz", "MobileGamer.biz", "gaming", gn("mobilegamer.biz"), 3),
    S("toucharcade", "TouchArcade", "gaming", "https://toucharcade.com/feed/", 3),
    S("148apps", "148Apps", "gaming", gn("148apps.com"), 3),
]

# ----------------------------------------------------------- technology ----
NEW += [
    S("techradar", "TechRadar", "technology", "https://www.techradar.com/feeds/rss", 2),
    S("pcmag", "PCMag", "technology", "https://www.pcmag.com/feeds/news", 2),
    S("gizmodo", "Gizmodo", "technology", "https://gizmodo.com/feed", 2),
    S("digitaltrends", "Digital Trends", "technology", "https://www.digitaltrends.com/feed", 3),
    S("zdnet", "ZDNet", "technology", "https://www.zdnet.com/news/rss.xml", 2),
    S("computerworld", "Computerworld", "technology", "https://www.computerworld.com/rss.xml", 3),
    S("techrepublic", "TechRepublic", "technology", "https://www.techrepublic.com/feed/", 3),
    S("anandtech", "AnandTech (archived)", "technology", gn("anandtech.com"), 3),
    S("guru3d", "Guru3D", "technology", "https://www.guru3d.com/headlines.xml", 3),
    S("notebookcheck", "Notebookcheck", "technology", gn("notebookcheck.net"), 3),
    S("notebookreview", "NotebookReview", "technology", gn("notebookreview.com"), 3),
    S("androidpolice", "Android Police", "technology", "https://www.androidpolice.com/feed/", 2),
    S("androidauthority", "Android Authority", "technology", "https://www.androidauthority.com/feed", 2),
    S("9to5google", "9to5Google", "technology", "https://9to5google.com/feed/", 2),
    S("macrumors", "MacRumors", "technology", "https://www.macrumors.com/feed/", 2),
    S("appleinsider", "AppleInsider", "technology", "https://appleinsider.com/articles.rss", 2),
    S("cultofmac", "Cult of Mac", "technology", "https://www.cultofmac.com/feed", 3),
    S("imore", "iMore", "technology", "https://imore.com/rss", 3),
    S("windowscentral", "Windows Central", "technology", "https://www.windowscentral.com/rss/full", 2),
    S("neowin", "NeoWin", "technology", "https://www.neowin.net/news/rss.xml", 2),
    S("onmsft", "OnMSFT", "technology", gn("onmsft.com"), 3),
    S("ghacks", "GHacks", "technology", "https://www.ghacks.net/feed/", 3),
    S("betanews", "BetaNews", "technology", "https://betanews.com/feed/", 3),
    S("softpedia", "Softpedia", "technology", "https://www.softpedia.com/newsRSS.shtml", 3),
    S("majorgeeks", "MajorGeeks", "technology", "https://majorgeeks.com/rss.xml", 3),
    S("filehippo", "FileHippo", "technology", gn("filehippo.com"), 3),
    S("fossbytes", "FossBytes", "technology", "https://fossbytes.com/feed/", 3),
    S("makeuseof", "MakeUseOf", "technology", "https://www.makeuseof.com/rss/", 2),
    S("howtogeek", "How-To Geek", "technology", "https://www.howtogeek.com/feed", 2),
    S("lifehacker", "Lifehacker", "technology", "https://lifehacker.com/rss", 2),
    S("slashdot", "Slashdot", "technology", "https://rss.slashdot.org/Slashdot/slashdot", 2),
    S("extremetech", "ExtremeTech", "technology", "https://extremetech.com/feed", 3),
    S("techspot", "TechSpot", "technology", "https://www.techspot.com/news/rss.xml", 2),
    S("hexus", "Hexus", "technology", gn("hexus.net"), 3),
    S("kitguru", "KitGuru", "technology", "https://www.kitguru.net/feed/", 3),
    S("overclock3d", "Overclock3D", "technology", gn("overclock3d.net"), 3),
    S("tweaktown", "TweakTown", "technology", gn("tweaktown.com"), 3),
    S("pcworld", "PCWorld", "technology", "https://www.pcworld.com/homepage/rss.xml", 2),
    S("mashable", "Mashable", "technology", gn("mashable.com"), 3),
    S("fastcompany", "Fast Company", "technology", gn("fastcompany.com"), 3),
    S("quartz", "Quartz", "technology", "https://qz.com/arc/outboundfeeds/rss/", 2),
    S("protocol", "Protocol", "technology", gn("protocol.com"), 3),
    S("theinformation", "The Information", "technology", gn("theinformation.com"), 3),
    S("semafor", "Semafor", "technology", gn("semafor.com"), 3),
    S("axios-tech", "Axios Tech", "technology", "https://feeds.axios.com/axios/Technology", 2),
    S("restofworld", "Rest of World", "technology", "https://restofworld.org/feed/", 2),
    S("thenextweb", "The Next Web", "technology", "https://thenextweb.com/feed", 3),
    S("siliconangle", "SiliconANGLE", "technology", "https://siliconangle.com/feed/", 3),
    S("blocksandfiles", "Blocks & Files", "technology", "https://blocksandfiles.com/feed/", 3),
    S("channelnewsasia", "CNA Tech", "technology", gn("channelnewsasia.com"), 2),
    S("techinasia", "Tech in Asia", "technology", "https://www.techinasia.com/feed", 3),
    S("e27", "e27", "technology", "https://e27.co/feed/", 3),
]

# ----------------------------------------------------------- software-dev --
NEW += [
    S("hn-official", "Hacker News (official)", "software-dev", "https://news.ycombinator.com/rss", 1),
    S("lobsters", "Lobsters", "software-dev", "https://lobste.rs/rss", 2),
    S("infoq", "InfoQ", "software-dev", "https://www.infoq.com/feed/", 2),
    S("thenewstack", "The New Stack", "software-dev", "https://thenewstack.io/feed/", 2),
    S("sdtimes", "SDTimes", "software-dev", gn("sdtimes.com"), 3),
    S("dzone", "DZone", "software-dev", "https://dzone.com/rss", 2),
    S("github-blog", "GitHub Blog", "software-dev", "https://github.blog/feed/", 1),
    S("stackoverflow-blog", "Stack Overflow Blog", "software-dev", "https://stackoverflow.blog/feed/", 2),
    S("devto", "dev.to", "software-dev", "https://dev.to/feed", 2),
    S("infoworld", "InfoWorld", "software-dev", "https://www.infoworld.com/article/rss.xml", 3),
    S("martinfowler", "Martin Fowler", "software-dev", "https://martinfowler.com/feed.atom", 1),
    S("sedaily", "Software Engineering Daily", "software-dev", gn("softwareengineeringdaily.com"), 3),
    S("changelog", "Changelog", "software-dev", gn("changelog.com"), 3),
    S("softwareleadweekly", "Software Lead Weekly", "software-dev", gn("softwareleadweekly.com"), 3),
    S("console-dev", "Console.dev", "software-dev", "https://blog.console.dev/rss.xml", 2),
    S("bytesdev", "Bytes.dev", "software-dev", gn("bytes.dev"), 3),
    S("pointer-io", "Pointer", "software-dev", gn("pointer.io"), 3),
    S("dailydev", "daily.dev", "software-dev", gn("daily.dev"), 3),
    S("hackernoon", "HackerNoon", "software-dev", gn("hackernoon.com"), 3),
    S("freecodecamp", "freeCodeCamp News", "software-dev", "https://www.freecodecamp.org/news/rss/", 2),
    S("realpython", "Real Python", "software-dev", gn("realpython.com"), 3),
    S("pythoninsider", "Python Insider", "software-dev", "https://pythoninsider.blogspot.com/feeds/posts/default", 3),
    S("planetpython", "Planet Python", "software-dev", "https://planetpython.org/atom.xml", 2),
    S("pythontutorial", "Python Tutorial", "software-dev", gn("pythontutorial.net"), 3),
    S("pythonweekly", "Python Weekly", "software-dev", gn("pythonweekly.com"), 3),
    S("javascriptweekly", "JavaScript Weekly", "software-dev", gn("javascriptweekly.com"), 3),
    S("nodeweekly", "Node Weekly", "software-dev", gn("nodeweekly.com"), 3),
    S("react-status-code", "React Status Code", "software-dev", "https://react.statuscode.com/feed", 2),
    S("frontendfocus", "Frontend Focus", "software-dev", gn("frontendfoc.us"), 3),
    S("css-tricks", "CSS-Tricks", "software-dev", "https://css-tricks.com/feed/", 2),
    S("smashingmag", "Smashing Magazine", "software-dev", "https://www.smashingmagazine.com/feed/", 2),
    S("webdev", "web.dev", "software-dev", "https://web.dev/feed/", 2),
    S("chrome-devrel", "Chrome for Developers", "software-dev", gn("developer.chrome.com"), 3),
    S("mdn", "MDN Web Docs", "software-dev", gn("developer.mozilla.org"), 3),
    S("nextjs-blog", "Next.js Blog", "software-dev", gn("nextjs.org"), 3),
    S("vercel-blog", "Vercel Blog", "software-dev", gn("vercel.com"), 3),
    S("netlify-blog", "Netlify Blog", "software-dev", gn("netlify.com"), 3),
    S("cloudflare-blog", "Cloudflare Blog", "software-dev", "https://blog.cloudflare.com/rss/", 1),
    S("aws-blogs", "AWS News Blog", "software-dev", "https://aws.amazon.com/blogs/aws/feed/", 2),
    S("azure-blog", "Azure Blog", "software-dev", "https://azure.microsoft.com/en-us/blog/feed/", 2),
    S("kubernetes-blog", "Kubernetes Blog", "software-dev", "https://kubernetes.io/feed.xml", 1),
    S("docker-blog", "Docker Blog", "software-dev", "https://www.docker.com/blog/feed/", 2),
    S("meta-eng", "Meta Engineering", "software-dev", gn("engineering.fb.com"), 3),
    S("netflix-techblog", "Netflix Tech Blog", "software-dev", "https://netflixtechblog.com/feed", 2),
    S("slack-eng", "Slack Engineering", "software-dev", gn("slack.engineering"), 3),
    S("uber-eng", "Uber Engineering", "software-dev", gn("uber.com"), 3),
    S("airbnb-tech", "Airbnb Tech", "software-dev", "https://medium.com/airbnb-tech/feed", 2),
    S("shopify-eng", "Shopify Engineering", "software-dev", gn("shopify.engineering"), 3),
    S("dropbox-tech", "Dropbox Tech", "software-dev", gn("dropbox.tech"), 3),
    S("discord-blog", "Discord Blog", "software-dev", gn("discord.com"), 3),
    S("spotify-eng", "Spotify Engineering", "software-dev", gn("engineering.atspotify.com"), 3),
    S("stripe-eng", "Stripe Engineering", "software-dev", gn("stripe.com"), 3),
    S("segment-blog", "Segment Blog", "software-dev", gn("segment.com"), 3),
    S("datadog-blog", "Datadog Blog", "software-dev", gn("datadoghq.com"), 3),
    S("linkedin-eng", "LinkedIn Engineering", "software-dev", gn("engineering.linkedin.com"), 3),
    S("pragmaticengineer", "The Pragmatic Engineer", "software-dev", "https://blog.pragmaticengineer.com/rss/", 2),
    S("highscalability", "High Scalability", "software-dev", gn("highscalability.com"), 3),
    S("bytebytego", "ByteByteGo", "software-dev", gn("bytebytego.com"), 3),
    S("systemdesign-one", "System Design One", "software-dev", gn("systemdesign.one"), 3),
    S("systemdesignprimer", "System Design Primer", "software-dev", gn("systemdesignprimer.com"), 3),
    S("devinterrupted", "Dev Interrupted", "software-dev", gn("devinterrupted.com"), 3),
    S("architecture-center", "Software Architecture Center", "software-dev", gn("architecture-center.com"), 3),
    S("microservices-io", "Microservices.io", "software-dev", gn("microservices.io"), 3),
    S("theserverside", "The Server Side", "software-dev", gn("theserverside.com"), 3),
    S("baeldung", "Baeldung", "software-dev", "https://www.baeldung.com/feed", 2),
    S("reflectoring", "Reflectoring", "software-dev", gn("reflectoring.io"), 3),
    S("testcontainers", "Testcontainers", "software-dev", gn("testcontainers.com"), 3),
    S("junit", "JUnit", "software-dev", gn("junit.org"), 3),
    S("thoughtworks-insights", "ThoughtWorks Insights", "software-dev", gn("thoughtworks.com"), 2),
    S("codinghorror", "Coding Horror", "software-dev", "https://codinghorror.wordpress.com/feed", 2),
    S("joelonsoftware", "Joel on Software", "software-dev", "https://www.joelonsoftware.com/feed/", 2),
    S("jetbrains-blog", "JetBrains Blog", "software-dev", "https://blog.jetbrains.com/feed/", 2),
    S("visualstudiomag", "Visual Studio Magazine", "software-dev", gn("visualstudiomagazine.com"), 3),
    S("rust-blog", "Rust Blog", "software-dev", "https://blog.rust-lang.org/atom.xml", 1),
    S("go-blog", "Go Blog", "software-dev", "https://go.dev/blog/feed.atom", 1),
    S("cpp-isocpp", "C++ Standards (ISO)", "software-dev", gn("isocpp.org"), 3),
    S("cppstories", "C++ Stories", "software-dev", gn("cppstories.com"), 3),
    S("scala-news", "Scala News", "software-dev", gn("scala-lang.org"), 3),
    S("kotlin-blog", "Kotlin Blog", "software-dev", gn("kotlinlang.org"), 3),
    S("elixir-blog", "Elixir Blog", "software-dev", gn("elixir-lang.org"), 3),
    S("ruby-news", "Ruby Language News", "software-dev", "https://www.ruby-lang.org/en/news/atom.xml", 2),
    S("rails-news", "Rails News", "software-dev", gn("rubyonrails.org"), 2),
    S("php-watch", "PHP Watch", "software-dev", "https://php.watch/feed/", 2),
    S("perl-com", "Perl.com", "software-dev", gn("perl.com"), 3),
    S("haskell-news", "Haskell News", "software-dev", gn("haskell.org"), 3),
    S("ocaml-news", "OCaml News", "software-dev", gn("ocaml.org"), 3),
    S("nixos-blog", "NixOS Blog", "software-dev", gn("nixos.org"), 3),
    S("opensource-com", "Open Source.com", "software-dev", gn("opensource.com"), 2),
    S("osi-blog", "OSI Blog", "software-dev", gn("opensource.org"), 3),
    S("lwn", "LWN.net", "software-dev", "https://lwn.net/headlines/rss", 1),
    S("kernel-org", "kernel.org", "software-dev", gn("kernel.org"), 2),
    S("kernelnewbies", "Kernel Newbies", "software-dev", gn("kernelnewbies.org"), 3),
]

# ------------------------------------------------------------------ ai-ml --
NEW += [
    S("deeplearning-batch", "DeepLearning.AI The Batch", "ai-ml", "https://www.deeplearning.ai/the-batch/feed/", 1),
    S("marktechpost", "MarkTechPost", "ai-ml", "https://www.marktechpost.com/feed/", 3),
    S("huggingface-blog", "Hugging Face Blog", "ai-ml", gn("huggingface.co"), 2),
    S("openai-news", "OpenAI News", "ai-ml", "https://openai.com/news/rss.xml", 1),
    S("deepmind-blog", "Google DeepMind Blog", "ai-ml", gn("deepmind.google"), 1),
    S("anthropic-news", "Anthropic News", "ai-ml", gn("anthropic.com"), 1),
    S("jack-clark", "Jack Clark (Import AI)", "ai-ml", "https://jack-clark.net/feed", 2),
    S("arxiv-csai", "arXiv cs.AI", "ai-ml", "http://export.arxiv.org/rss/cs.AI", 1),
    S("paperswithcode", "Papers with Code", "ai-ml", gn("paperswithcode.com"), 3),
    S("mlmastery", "Machine Learning Mastery", "ai-ml", "https://machinelearningmastery.com/feed/", 3),
    S("towardsdatascience", "Towards Data Science", "ai-ml", "https://towardsdatascience.com/feed", 2),
    S("analyticsvidhya", "Analytics Vidhya", "ai-ml", "https://analyticsvidhya.com/feed", 3),
    S("kdnuggets", "KDnuggets", "ai-ml", "https://www.kdnuggets.com/feed", 2),
    S("google-ai-blog", "Google AI Blog", "ai-ml", "https://ai.googleblog.com/feeds/posts/default", 1),
    S("google-research", "Google Research Blog", "ai-ml", "https://research.google/blog/rss/", 1),
    S("meta-ai", "Meta AI Blog", "ai-ml", gn("ai.meta.com"), 2),
    S("nvidia-blog", "NVIDIA Blog", "ai-ml", "https://blogs.nvidia.com/feed/", 2),
    S("aws-ai-blog", "AWS AI Blog", "ai-ml", "https://aws.amazon.com/blogs/ai/feed/", 2),
    S("pytorch-blog", "PyTorch Blog", "ai-ml", gn("pytorch.org"), 2),
    S("tensorflow-blog", "TensorFlow Blog", "ai-ml", "https://blog.tensorflow.org/feed", 1),
    S("keras", "Keras", "ai-ml", gn("keras.io"), 3),
    S("sklearn-whatsnew", "scikit-learn What's New", "ai-ml", gn("scikit-learn.org"), 2),
    S("fastai", "fast.ai", "ai-ml", gn("fast.ai"), 2),
    S("distill", "Distill", "ai-ml", "https://distill.pub/rss.xml", 2),
    S("colah", "Chris Olah's Blog", "ai-ml", "https://colah.github.io/rss.xml", 1),
    S("lilianweng", "Lil'Log", "ai-ml", gn("lilianweng.github.io"), 2),
    S("raschka", "Ahead of AI (S. Raschka)", "ai-ml", gn("sebastianraschka.com"), 2),
    S("chiphuyen", "Chip Huyen's Blog", "ai-ml", "https://huyenchip.com/feed.xml", 2),
    S("thegradient", "The Gradient", "ai-ml", gn("thegradient.pub"), 3),
    S("importai", "Import AI", "ai-ml", "https://importai.substack.com/feed", 2),
    S("lastweekinai", "Last Week in AI", "ai-ml", "https://lastweekin.ai/feed", 2),
    S("bitterli", "Benedikt Bitterli", "ai-ml", gn("benediktbitterli.me"), 3),
    S("latent-space", "Latent Space", "ai-ml", "https://www.latent.space/feed", 2),
    S("the-decoder", "The Decoder", "ai-ml", "https://the-decoder.com/feed/", 2),
    S("ainews", "AI News", "ai-ml", "https://artificialintelligence-news.com/feed/", 2),
    S("unite-ai", "Unite.ai", "ai-ml", gn("unite.ai"), 3),
    S("ai-news-com", "AI-News.com", "ai-ml", gn("ai-news.com"), 3),
    S("theresanaiforthat", "There's An AI For That", "ai-ml", gn("theresanaiforthat.com"), 3),
    S("futuretools", "FutureTools", "ai-ml", gn("futuretools.io"), 3),
    S("aitools-fyi", "AITools.fyi", "ai-ml", gn("aitools.fyi"), 3),
    S("producthunt-ai", "Product Hunt (AI)", "ai-ml", gn_query("site:producthunt.com artificial intelligence"), 3),
    S("replicate-blog", "Replicate Blog", "ai-ml", gn("replicate.com"), 3),
    S("modal-blog", "Modal Blog", "ai-ml", gn("modal.com"), 3),
    S("together-blog", "Together AI Blog", "ai-ml", gn("together.ai"), 3),
    S("fireworks-blog", "Fireworks AI Blog", "ai-ml", gn("fireworks.ai"), 3),
    S("perplexity-hub", "Perplexity Hub", "ai-ml", gn("perplexity.ai"), 3),
    S("mistral-news", "Mistral News", "ai-ml", gn("mistral.ai"), 2),
    S("cohere-blog", "Cohere Blog", "ai-ml", gn("cohere.com"), 2),
    S("ai21-blog", "AI21 Blog", "ai-ml", gn("ai21.com"), 3),
    S("stability-news", "Stability AI News", "ai-ml", gn("stability.ai"), 3),
    S("runway-news", "Runway News", "ai-ml", gn("runwayml.com"), 3),
    S("midjourney", "Midjourney", "ai-ml", gn("midjourney.com"), 3),
    S("bfl", "Black Forest Labs", "ai-ml", gn("blackforestlabs.ai"), 3),
    S("ollama-blog", "Ollama Blog", "ai-ml", gn("ollama.com"), 2),
    S("lmstudio-blog", "LM Studio Blog", "ai-ml", gn("lmstudio.ai"), 3),
    S("unsloth-blog", "Unsloth Blog", "ai-ml", gn("unsloth.ai"), 3),
    S("llamaindex-blog", "LlamaIndex Blog", "ai-ml", gn("llamaindex.ai"), 3),
    S("langchain-blog", "LangChain Blog", "ai-ml", "https://blog.langchain.com/rss.xml", 2),
    S("crewai-blog", "CrewAI Blog", "ai-ml", gn("crewai.com"), 3),
    S("haystack-blog", "Haystack Blog", "ai-ml", gn("haystack.deepset.ai"), 3),
    S("dspy", "DSPy", "ai-ml", gn("dspy.ai"), 3),
    S("vllm-blog", "vLLM Blog", "ai-ml", "https://blog.vllm.ai/feed/", 2),
    S("sglang-blog", "SGLang Blog", "ai-ml", gn("sglang.ai"), 3),
    S("llamacpp-releases", "llama.cpp Releases", "ai-ml", "https://github.com/ggml-org/llama.cpp/releases.atom", 2),
    S("ggml", "GGML", "ai-ml", gn("ggml.ai"), 3),
    S("eleuther", "EleutherAI", "ai-ml", gn("eleuther.ai"), 3),
    S("bigscience", "Big Science", "ai-ml", gn("bigscience.huggingface.co"), 3),
    S("anthropic-alignment", "Anthropic Alignment", "ai-ml", gn("alignment.anthropic.com"), 2),
    S("transformer-circuits", "Transformer Circuits", "ai-ml", gn("transformer-circuits.pub"), 1),
    S("lesswrong", "LessWrong", "ai-ml", "https://www.lesswrong.com/feed.xml", 2),
    S("alignmentforum", "Alignment Forum", "ai-ml", "https://www.alignmentforum.org/feed.xml", 2),
    S("epoch-ai", "Epoch AI", "ai-ml", gn("epoch.ai"), 2),
    S("metaculus", "Metaculus", "ai-ml", gn("metaculus.com"), 3),
    S("aiimpacts", "AI Impacts", "ai-ml", gn("aiimpacts.org"), 3),
    S("governance-ai", "Governance.ai", "ai-ml", gn("governance.ai"), 3),
    S("lawfare", "Lawfare (AI)", "ai-ml", gn("lawfaremedia.org"), 3),
    S("cais", "Center for AI Safety", "ai-ml", gn("centerforaisafety.com"), 3),
    S("futureoflife", "Future of Life Institute", "ai-ml", "https://futureoflife.org/feed/", 2),
    S("aiindex", "Stanford AI Index", "ai-ml", gn("aiindex.stanford.edu"), 2),
    S("hai-stanford", "Stanford HAI", "ai-ml", gn("hai.stanford.edu"), 3),
    S("bair", "BAIR Berkeley", "ai-ml", gn("bair.berkeley.edu"), 3),
    S("vectorinstitute", "Vector Institute", "ai-ml", gn("vectorinstitute.ai"), 3),
    S("mila", "Mila Quebec", "ai-ml", gn("mila.quebec"), 3),
    S("allenai", "Allen Institute for AI", "ai-ml", gn("allenai.org"), 2),
    S("ibm-research-blog", "IBM Research Blog", "ai-ml", gn("research.ibm.com"), 2),
    S("ibm-think-ai", "IBM Think: AI", "ai-ml", gn("ibm.com think ai"), 3),
    S("google-devs-blog", "Google Developers Blog", "ai-ml", "https://developers.googleblog.com/feeds/posts/default?atom", 1),
]

# ------------------------------------------------------------------ india --
NEW += [
    S("thehindu", "The Hindu", "india", "https://www.thehindu.com/news/national/feeder/default.rss", 1),
    S("indianexpress", "Indian Express", "india", "https://indianexpress.com/feed/", 2),
    S("ndtv", "NDTV", "india", "https://feeds.feedburner.com/ndtvnews-top-stories", 1),
    S("indiatoday", "India Today", "india", gn("indiatoday.in"), 1),
    S("theprint", "The Print", "india", gn("theprint.in"), 2),
    S("scroll-in", "Scroll.in", "india", "https://scroll.in/feed", 2),
    S("livemint", "Livemint", "india", gn("livemint.com"), 1),
    S("business-standard", "Business Standard", "india", gn("business-standard.com"), 2),
    S("timesofindia", "The Times of India", "india", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", 1),
    S("hindustantimes", "Hindustan Times", "india", "https://www.hindustantimes.com/rss/headlines/newsfeeds.rss", 1),
    S("telegraphindia", "The Telegraph", "india", gn("telegraphindia.com"), 2),
    S("deccanherald", "Deccan Herald", "india", gn("deccanherald.com"), 3),
    S("theweek-in", "The Week", "india", gn("theweek.in"), 3),
    S("outlookindia", "Outlook India", "india", gn("outlookindia.com"), 2),
    S("firstpost", "Firstpost", "india", gn("firstpost.com"), 2),
    S("news18", "News18", "india", gn("news18.com"), 2),
    S("cnnnews18", "CNN-News18", "india", gn("cnnnews18.com"), 2),
    S("cnbctv18", "CNBC-TV18", "india", gn("cnbctv18.com"), 2),
    S("moneycontrol", "Moneycontrol", "india", gn("moneycontrol.com"), 2),
    S("economictimes", "Economic Times", "india", "https://economictimes.indiatimes.com/rssfeedstopstories.cms", 1),
    S("financialexpress", "Financial Express", "india", gn("financialexpress.com"), 3),
    S("businessline", "Business Line", "india", gn("businessline.com"), 2),
    S("fortuneindia", "Fortune India", "india", gn("fortuneindia.com"), 3),
    S("outlookbusiness", "Outlook Business", "india", gn("outlookbusiness.com"), 3),
    S("vccircle", "VC Circle", "india", gn("vccircle.com"), 3),
    S("analyticsindiamag", "Analytics India Magazine", "india", gn("analyticsindiamag.com"), 3),
    S("yourstory", "YourStory", "india", gn("yourstory.com"), 2),
    S("inc42", "Inc42", "india", gn("inc42.com"), 3),
    S("medianama", "MediaNama", "india", "https://www.medianama.com/feed/", 3),
    S("entrackr", "Entrackr", "india", gn("entrackr.com"), 3),
    S("the-ken", "The Ken", "india", "https://the-ken.com/feed", 2),
    S("faktordaily", "Factor Daily", "india", gn("faktordaily.com"), 3),
    S("newslaundry", "NewsLaundry", "india", gn("newslaundry.com"), 2),
    S("thewire", "The Wire", "india", "https://thewire.in/feed.xml", 1),
    S("thequint", "The Quint", "india", gn("thequint.com"), 2),
    S("altnews-in", "AltNews", "india", gn("altnews.in"), 3),
    S("boomlive", "Boom Live", "india", gn("boomlive.in"), 2),
    S("factly", "Factly", "india", gn("factly.in"), 3),
    S("thelogicalindian", "The Logical Indian", "india", gn("thelogicalindian.com"), 3),
    S("indiaspend", "IndiaSpend", "india", "https://www.indiaspend.org/feed", 2),
    S("caravanmagazine", "Caravan Magazine", "india", gn("caravanmagazine.in"), 3),
    S("frontline", "Frontline", "india", gn("frontline.thehindu.com"), 2),
    S("epw", "EPW", "india", gn("epw.in"), 2),
    S("orf", "ORF", "india", gn("orfonline.org"), 3),
    S("idsa", "IDSA", "india", gn("idsa.in"), 3),
    S("takshashila", "Takshashila", "india", gn("takshashila.org.in"), 3),
    S("prsindia", "PRS India", "india", gn("prsindia.org"), 2),
    S("vidhi", "Vidhi Centre", "india", gn("vidhi.org"), 3),
    S("cprindia", "CPR India", "india", gn("cprindia.org"), 3),
    S("carnegieindia", "Carnegie India", "india", gn("carnegieindia.com"), 3),
    S("gatewayhouse", "Gateway House", "india", gn("gatewayhouse.in"), 3),
    S("observerresearch", "Observer Research Foundation", "india", gn("observerresearchfoundation.org"), 3),
    S("pib", "PIB", "india", "https://pib.gov.in/RSSFeed.xml", 1),
    S("pmindia", "PM India", "india", gn("pmindia.gov.in"), 2),
    S("mea", "MEA India", "india", gn("mea.gov.in"), 2),
    S("mospi", "MoSPI", "india", gn("mospi.gov.in"), 2),
    S("rbi", "RBI", "india", "https://www.rbi.org.in/rssfeeds/PressReleaseRSS.xml", 1),
    S("sebi", "SEBI", "india", gn("sebi.gov.in"), 2),
    S("nseindia", "NSE India", "india", gn("nseindia.com"), 2),
    S("bseindia", "BSE India", "india", gn("bseindia.com"), 2),
    S("startupindia", "Startup India", "india", gn("startupindia.gov.in"), 3),
    S("meity", "MeitY", "india", gn("meity.gov.in"), 3),
    S("indiaai", "IndiaAI", "india", gn("indiaai.gov.in"), 3),
    S("isro", "ISRO", "india", gn("isro.gov.in"), 2),
    S("drdo", "DRDO", "india", gn("drdo.gov.in"), 3),
    S("sansad", "Sansad TV", "india", gn("sansad.in"), 3),
    S("eci", "Election Commission of India", "india", gn("eci.gov.in"), 3),
    S("livelaw", "LiveLaw", "india", gn("livelaw.in"), 3),
    S("barandbench", "Bar & Bench", "india", gn("barandbench.com"), 3),
    S("lawbeat", "LawBeat", "india", gn("lawbeat.in"), 3),
    S("taxmann", "Taxmann", "india", gn("taxmann.com"), 3),
    S("cleartax", "ClearTax", "india", gn("cleartax.in"), 3),
    S("vakilsearch", "VakilSearch", "india", gn("vakilsearch.com"), 3),
    S("techcircle", "TechCircle", "india", gn("techcircle.in"), 3),
    S("expresscomputer", "Express Computer", "india", gn("expresscomputer.in"), 3),
    S("cio-india", "CIO India", "india", gn("cio.com"), 3),
    S("itvoice", "IT Voice", "india", gn("itvoice.in"), 3),
    S("cioreviewindia", "CIO Review India", "india", gn("cioreviewindia.com"), 3),
    S("expresspharma", "Express Pharma", "india", gn("expresspharma.in"), 3),
    S("team-bhp", "Team-BHP", "india", gn("team-bhp.com"), 2),
    S("sportskeeda", "Sportskeeda", "india", gn("sportskeeda.com"), 3),
    S("cricbuzz", "Cricbuzz", "india", gn("cricbuzz.com"), 2),
    S("espncricinfo", "ESPNcricinfo", "india", gn("espncricinfo.com"), 2),
    S("olympics-india", "Olympics India News", "india", gn_query("site:olympics.com india"), 3),
]

# ------------------------------------------------------------------- cars --
NEW += [
    S("topgear", "Top Gear", "cars", "https://www.topgear.com/rss.xml", 2),
    S("motor1", "Motor1", "cars", "https://www.motor1.com/feed", 2),
    S("caranddriver", "Car and Driver", "cars", gn("caranddriver.com"), 2),
    S("thedrive", "The Drive", "cars", gn("thedrive.com"), 2),
    S("autoblog", "Autoblog", "cars", "https://autoblog.com/feed", 2),
    S("carscoops", "CarsCoops", "cars", "https://carscoops.com/feed", 3),
    S("jalopnik", "Jalopnik", "cars", "https://jalopnik.com/rss.xml", 2),
    S("roadandtrack", "Road & Track", "cars", gn("roadandtrack.com"), 2),
    S("motortrend", "MotorTrend", "cars", gn("motortrend.com"), 2),
    S("automobilemag", "Automobile Mag", "cars", gn("automobilemag.com"), 3),
    S("evo-uk", "evo", "cars", gn("evo.co.uk"), 3),
    S("carwow", "Carwow", "cars", gn("carwow.co.uk"), 3),
    S("pistonheads", "PistonHeads", "cars", gn("pistonheads.com"), 3),
    S("honestjohn", "Honest John", "cars", gn("honestjohn.co.uk"), 3),
    S("autoexpress", "Auto Express", "cars", gn("autoexpress.co.uk"), 2),
    S("autocar-uk", "Autocar UK", "cars", gn("autocar.co.uk"), 2),
    S("whatcar", "What Car?", "cars", gn("whatcar.com"), 3),
    S("carbuzz", "CarBuzz", "cars", "https://www.carbuzz.com/rss.xml", 2),
    S("supercars-net", "Supercars.net", "cars", gn("supercars.net"), 3),
    S("gtspirit", "GTSpirit", "cars", gn("gtspirit.com"), 3),
    S("goodwood", "Goodwood", "cars", gn("goodwood.com"), 2),
    S("bringatrailer", "Bring a Trailer", "cars", "https://bringatrailer.com/feed", 2),
    S("classicdriver", "Classic Driver", "cars", gn("classicdriver.com"), 3),
    S("hagerty", "Hagerty Media", "cars", gn("hagerty.com"), 3),
    S("speedhunters", "Speedhunters", "cars", "https://www.speedhunters.com/feed/", 2),
    S("drivetastefully", "Drive Tastefully", "cars", gn("drivetastefully.com"), 3),
    S("petrolicious", "Petrolicious", "cars", "https://petrolicious.com/feed", 2),
    S("autocarindia", "AutoCar India", "cars", gn("autocarindia.com"), 2),
]

# --------------------------------------------------------------------- f1 --
NEW += [
    S("formula1", "Formula 1 Official", "f1", gn("formula1.com"), 1),
    S("fia", "FIA", "f1", gn("fia.com"), 2),
    S("motorsport-com", "Motorsport.com", "f1", "https://www.motorsport.com/rss/", 2),
    S("autosport", "Autosport", "f1", gn("autosport.com"), 2),
    S("racingnews365", "RacingNews365", "f1", "https://racingnews365.com/feed", 2),
    S("the-race", "The Race", "f1", "https://the-race.com/feed/", 2),
    S("racer-com", "Racer", "f1", gn("racer.com"), 3),
    S("dailysportscar", "Daily Sportscar", "f1", gn("dailysportscar.com"), 3),
    S("sportscar365", "Sportscar365", "f1", gn("sportscar365.com"), 3),
    S("dirtfish", "DirtFish", "f1", gn("dirtfish.com"), 3),
    S("nascar", "NASCAR", "f1", gn("nascar.com"), 2),
    S("indycar", "IndyCar", "f1", gn("indycar.com"), 3),
    S("motogp", "MotoGP", "f1", gn("motogp.com"), 3),
    S("worldsbk", "WorldSBK", "f1", gn("worldsbk.com"), 3),
    S("wrc", "WRC", "f1", gn("wrc.com"), 3),
    S("fiawec", "FIA WEC", "f1", gn("fiawec.com"), 3),
    S("imsa", "IMSA", "f1", gn("imsa.com"), 3),
]

# --------------------------------------------------------- entertainment --
NEW += [
    S("hollywoodreporter", "The Hollywood Reporter", "entertainment", "https://www.hollywoodreporter.com/?format=rss", 2),
    S("variety", "Variety", "entertainment", "https://variety.com/feed/", 1),
    S("deadline", "Deadline", "entertainment", "https://deadline.com/feed/", 1),
    S("indiewire", "IndieWire", "entertainment", "https://www.indiewire.com/feed", 2),
    S("thewrap", "The Wrap", "entertainment", gn("thewrap.com"), 2),
    S("collider", "Collider", "entertainment", "https://collider.com/feed", 3),
    S("empireonline", "Empire", "entertainment", "https://www.empireonline.com/feed/", 2),
    S("screenrant", "Screen Rant", "entertainment", "https://screenrant.com/feed", 2),
    S("avclub", "A.V. Club", "entertainment", "https://www.avclub.com/rss", 2),
    S("rogererebert", "RogerEbert.com", "entertainment", gn("rogererebert.com"), 3),
    S("letterboxd", "Letterboxd", "entertainment", gn("letterboxd.com"), 3),
    S("imdb", "IMDb", "entertainment", gn("imdb.com"), 2),
    S("rottentomatoes", "Rotten Tomatoes", "entertainment", gn("rottentomatoes.com"), 2),
    S("metacritic", "Metacritic", "entertainment", gn("metacritic.com"), 2),
    S("boxofficemojo", "Box Office Mojo", "entertainment", gn("boxofficemojo.com"), 3),
    S("the-numbers", "The Numbers", "entertainment", gn("the-numbers.com"), 3),
    S("billboard", "Billboard", "entertainment", gn("billboard.com"), 2),
    S("rollingstone", "Rolling Stone", "entertainment", "https://www.rollingstone.com/rss.xml", 2),
    S("pitchfork", "Pitchfork", "entertainment", "https://pitchfork.com/feed/", 2),
    S("stereogum", "Stereogum", "entertainment", gn("stereogum.com"), 3),
    S("consequence", "Consequence", "entertainment", gn("consequence.net"), 3),
    S("nme", "NME", "entertainment", "https://www.nme.com/rss", 2),
    S("kerrang", "Kerrang!", "entertainment", gn("kerrang.com"), 3),
    S("loudersound", "Louder Sound", "entertainment", gn("loudersound.com"), 3),
    S("ultimateclassicrock", "Ultimate Classic Rock", "entertainment", gn("ultimateclassicrock.com"), 3),
    S("spin-mag", "SPIN", "entertainment", "https://www.spin.com/feed", 2),
    S("complex", "Complex", "entertainment", gn("complex.com"), 3),
    S("hypebeast", "Hypebeast", "entertainment", "https://hypebeast.com/feed", 2),
    S("highsnobiety", "Highsnobiety", "entertainment", gn("highsnobiety.com"), 3),
    S("sneakernews", "Sneaker News", "entertainment", "https://www.sneakernews.com/feed", 2),
    S("fashionista", "Fashionista", "entertainment", gn("fashionista.com"), 3),
    S("thecut", "The Cut", "entertainment", "https://www.thecut.com/feed", 2),
    S("vulture", "Vulture", "entertainment", gn("vulture.com"), 3),
    S("people-com", "People", "entertainment", gn("people.com"), 3),
    S("eonline", "E! Online", "entertainment", gn("eonline.com"), 3),
    S("tmz", "TMZ", "entertainment", gn("tmz.com"), 3),
    S("pagesix", "Page Six", "entertainment", "https://pagesix.com/feed", 2),
    S("vanityfair", "Vanity Fair", "entertainment", gn("vanityfair.com"), 3),
    S("hollywood-com", "Hollywood.com", "entertainment", gn("hollywood.com"), 3),
    S("fandom-wiki", "Fandom", "entertainment", gn("fandom.com"), 3),
    S("tvline", "TVLine", "entertainment", "https://tvline.com/feed", 2),
    S("tvinsider", "TV Insider", "entertainment", gn("tvinsider.com"), 3),
    S("whats-on-netflix", "What's on Netflix", "entertainment", gn("whats-on-netflix.com"), 3),
    S("theplaylist", "The Playlist", "entertainment", gn("theplaylist.net"), 3),
    S("animenewsnetwork", "Anime News Network", "entertainment", "https://www.animenewsnetwork.com/all/news.rss", 1),
    S("crunchyroll-news", "Crunchyroll News", "entertainment", "https://news.crunchyroll.com/feed/", 2),
    S("comicbook", "ComicBook", "entertainment", "https://comicbook.com/feed", 2),
    S("cbr", "CBR", "entertainment", "https://cbr.com/feed", 3),
    S("vice", "Vice", "entertainment", gn("vice.com"), 3),
    S("knowyourmeme", "Know Your Meme", "entertainment", gn("knowyourmeme.com"), 3),
]

# ------------------------------------------------------------------ marvel --
NEW += [
    S("marvel-com", "Marvel Newsroom", "marvel", gn("marvel.com"), 1),
    S("marvelstudiosnews", "Marvel Studios News", "marvel", gn("marvelstudiosnews.com"), 3),
    S("thedirect", "The Direct", "marvel", gn("thedirect.com"), 2),
    S("superherohype", "Super Hero Hype", "marvel", gn("superherohype.com"), 3),
    S("superhero-news", "Superhero News", "marvel", gn("superhero-news.com"), 3),
    S("mcuconnection", "MCU Connection", "marvel", gn("mcuconnection.com"), 3),
    S("marvelblog", "Marvel Blog", "marvel", gn("marvelblog.com"), 3),
    S("mcu-fandom", "MCU Wiki (Fandom)", "marvel", "https://marvelcinematicuniverse.fandom.com/api.php?action=feedrecent&format=rss", 3),
    S("thecosmiccircus", "The Cosmic Circus", "marvel", gn("thecosmiccircus.com"), 3),
    S("cosmicbook", "Cosmic Book", "marvel", "https://cosmicbook.net/feed", 2),
    S("murphysmultiverse", "Murphy's Multiverse", "marvel", gn("murphysmultiverse.com"), 3),
    S("slashfilm", "/Film", "marvel", gn("slashfilm.com"), 3),
    S("cinemablend", "CinemaBlend", "marvel", gn("cinemablend.com"), 3),
    S("movieweb", "MovieWeb", "marvel", "https://movieweb.com/feed", 2),
    S("comingsoon", "ComingSoon.net", "marvel", gn("comingsoon.net"), 3),
    S("joblo", "JoBlo", "marvel", gn("joblo.com"), 3),
    S("denofgeek", "Den of Geek", "marvel", gn("denofgeek.com"), 3),
    S("inverse", "Inverse", "marvel", "https://inverse.com/feed", 2),
    S("syfy", "Syfy", "marvel", gn("syfy.com"), 3),
    S("fandomwire", "Fandom Wire", "marvel", gn("fandomwire.com"), 3),
    S("geektyrant", "GeekTyrant", "marvel", gn("geektyrant.com"), 3),
    S("geekvibesnation", "Geek Vibes Nation", "marvel", gn("geekvibesnation.com"), 3),
    S("geekculture", "Geek Culture", "marvel", gn("geekculture.co"), 3),
    S("comicbookmovie", "Comic Book Movie", "marvel", gn("comicbookmovie.com"), 3),
    S("superheroinsider", "Superhero Insider", "marvel", gn("superheroinsider.com"), 3),
    S("heroichollywood", "Heroic Hollywood", "marvel", gn("heroichollywood.com"), 3),
    S("geeksofcolor", "Geeks of Color", "marvel", gn("geeksofcolor.co"), 3),
    S("bleedingcool", "Bleeding Cool", "marvel", "https://www.bleedingcool.com/feed", 2),
    S("aiptcomics", "AIPT Comics", "marvel", gn("aiptcomics.com"), 3),
    S("comicsbeat", "Comics Beat", "marvel", gn("comicsbeat.com"), 3),
    S("comicbookherald", "Comic Book Herald", "marvel", gn("comicbookherald.com"), 3),
    S("comicsalliance", "Comics Alliance", "marvel", gn("comicsalliance.com"), 3),
    S("leagueofcomicgeeks", "League of Comic Geeks", "marvel", gn("leagueofcomicgeeks.com"), 3),
    S("comicbookroundup", "Comic Book Roundup", "marvel", gn("comicbookroundup.com"), 3),
    S("newsarama", "Newsarama", "marvel", gn("newsarama.com"), 3),
    S("multiversitycomics", "Multiversity Comics", "marvel", gn("multiversitycomics.com"), 3),
    S("thepopverse", "The Popverse", "marvel", gn("thepopverse.com"), 3),
    S("comicsxf", "ComicsXF", "marvel", gn("comicsxf.com"), 3),
    S("comicbookdispatch", "Comic Book Dispatch", "marvel", gn("comicbookdispatch.com"), 3),
    S("ladbible", "LADbible", "marvel", gn("ladbible.com"), 3),
    S("unilad", "UniLad", "marvel", gn("unilad.com"), 3),
    S("buzzfeed", "BuzzFeed", "marvel", "https://www.buzzfeed.com/feed", 2),
    S("ew", "Entertainment Weekly", "marvel", gn("ew.com"), 3),
    S("justjared", "Just Jared", "marvel", gn("justjared.com"), 3),
    S("hollywoodlife", "Hollywood Life", "marvel", gn("hollywoodlife.com"), 3),
    S("whats-on-disneyplus", "What's on Disney+", "marvel", gn("whats-on-disneyplus.com"), 3),
    S("thedisinsider", "The DisInsider", "marvel", gn("thedisinsider.com"), 3),
    S("disneyplus", "Disney+ News", "marvel", gn("disneyplus.com"), 3),
    S("d23", "D23", "marvel", gn("d23.com"), 3),
    S("disney-com", "Disney Newsroom", "marvel", gn("disney.com"), 3),
    S("reddit-marvelstudios", "r/MarvelStudios", "marvel", "https://www.reddit.com/r/MarvelStudios/.rss", 2),
    S("reddit-marvel-spoilers", "r/marvelstudiosspoilers", "marvel", "https://www.reddit.com/r/marvelstudiosspoilers/.rss", 3),
    S("reddit-marvel", "r/Marvel", "marvel", "https://www.reddit.com/r/Marvel/.rss", 2),
    S("reddit-comicbooks", "r/comicbooks", "marvel", "https://www.reddit.com/r/comicbooks/.rss", 3),
]

# -------------------------------------------------------------------- main --
import re
from urllib.parse import urlparse


def domain_of(url: str) -> str:
    """Normalized identity of the site a feed represents (for dedup).

    Native URLs use their host. Google News search feeds encode the target
    site in the `site:` query, so we recover it there; custom GN queries that
    carry no `site:` get a unique marker so they never collide.
    """
    from urllib.parse import parse_qs

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host == "news.google.com":
        q = (parse_qs(parsed.query).get("q") or [""])[0].strip()
        if q.lower().startswith("site:"):
            token = q[5:].strip().split()[0].lower()
            if not token:
                return "gn:" + quote_plus(q)
            host = token
        else:
            return "gn:" + quote_plus(q)
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    reg = ".".join(parts[-2:])
    if reg in PLATFORM_HOSTS:
        sub = parts[0] if len(parts) > 2 else None
        if sub and sub not in GENERIC_SUBDOMAINS:
            return f"{sub}.{reg}"
        segs = [p for p in parsed.path.split("/") if p]
        return reg + (f":{segs[0]}" if segs else "")
    # keep 3 labels for common ccTLD second levels (co.uk, com.au...)
    if len(parts) >= 3 and parts[-2] in {"co", "com", "org", "net", "gov"}:
        return ".".join(parts[-3:])
    return reg


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    raw = json.loads(CATALOG_PATH.read_text())
    if isinstance(raw, dict):  # tolerate {"sources": [...]} as well
        catalog = raw["sources"]
        wrapper = True
    else:
        catalog = raw
        wrapper = False
    existing_names = {s["name"] for s in catalog}
    existing_domains = {domain_of(s["url"]) for s in catalog}

    added, skipped_dup, seen_names, seen_domains = [], [], set(), set()
    for entry in NEW:
        name, url = entry["name"], entry["url"]
        dom = domain_of(url)
        if name in existing_names or name in seen_names:
            skipped_dup.append((name, "name already present"))
            continue
        multi = dom in MULTI_DOMAINS
        if not multi and (dom in existing_domains or dom in seen_domains):
            skipped_dup.append((name, f"domain {dom} already covered"))
            continue
        seen_names.add(name)
        seen_domains.add(dom)
        added.append(entry)

    catalog.extend(added)
    print(f"existing sources : {len(existing_names)}")
    print(f"batch entries    : {len(NEW)}")
    print(f"added            : {len(added)}")
    print(f"skipped (dup)    : {len(skipped_dup)}")
    for name, reason in skipped_dup:
        print(f"  - {name}: {reason}")
    if dry_run:
        print("dry run — catalog not modified")
        return
    payload = {"sources": catalog} if wrapper else catalog
    CATALOG_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"total sources    : {len(catalog)} -> {CATALOG_PATH}")


if __name__ == "__main__":
    main()
