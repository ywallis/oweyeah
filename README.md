# OweYeah
An app to help roommates deal with sharing the cost of furniture and its depreciation.

This app was created mainly to deal with the pain of people moving in and out of a flat.
If a chair was bought by two roommates, and one is moving out without the chair, how much will be owed?

## Usage

A core assumption is that the splitting of purchases is handled outside this app. The focus here is on moving in/out and transfer of ownership.

## Dev quickstart

This backend runs on FastAPI and uv. To get started, you must have uv installed.

When installed, simply run `uv run fastapi dev` and the backend server will be running.

The production version will use a postgres database. The development version runs on SQLite for quick iterations.

You can also use the docker image at https://hub.docker.com/r/ywallis/oweyeah-be

## Flat 

The core of the app is a shared flat.

## Users

A flat can have as many users as needed.

## Items

By default, items are shared by all members of a flat. Sometimes, items will only be shared by some of the flat users. It's possible to "exclude" users from an item.

Since we are unflexible and financially rigid, we have included a variety of options that allow for custom depreciation rates, as well as minimum thresholds for value.

## Moving in and moving out

Moving in and moving out functions abstract all details from the user.

Select which user should move in/out of an apartment, and you will receive a breakdown of what is owed to whom.

In the case of a move-in, it's possible to exclude specific items.

## Authentification

Most endpoints planned to be used in production already require authentication.
A JWT can be aquired at the `token` endpoint with a user email and password.

Google OAuth is also implemented. Although since the app is not verified by Google, users have to be manually added.

## Contributing

Contributions are highly welcome!
