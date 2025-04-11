window.onload = function () {
  // database module
  var database = (function (firebase) {
    firebase.initializeApp(getFirebaseConfig())

    return {
      query: queryDatabase,
      initialPoll: requestInitialPoll(),
      getCurrentPoll: getCurrentPoll,
      getInsertKey: getInsertKey
    }

    function getFirebaseConfig () {
      return {
        apiKey: '',
        authDomain: 'blind-game-poll.firebaseapp.com',
        databaseURL: 'https://blind-game-poll.firebaseio.com',
        projectId: 'blind-game-poll',
        storageBucket: 'blind-game-poll.appspot.com',
        messagingSenderId: '72922648857',
        appId: '1:72922648857:web:52ad5ce5e05b68bf4c3588'
      }
    }
    function getDatabase () {
      return firebase.database()
    }
    function queryDatabase (resource) {
      return getDatabase().ref(resource)
    }
    function requestInitialPoll () {
      return getCurrentPoll()
        .once('value')
        .then(function (snapshot) {
          return snapshot.val()
        })
    }
    function getCurrentPoll () {
      return queryDatabase('/polls/0')
    }
    function getInsertKey (resource) {
      return queryDatabase()
        .child(resource)
        .push().key
    }
  })(window.firebase)

  // poll render module
  var render = (function (database) {
    var rootContainer = document.getElementById('interactive-blind-poll')

    return database.initialPoll.then(function (pollData) {
      var pollOptions = getPollOptions(pollData)

      var pollAuthElement = createTextInputElement(
        'pollAuthKey',
        'truhenschluessel-eingabe'
      )

      var pollAuthLabel = createLabelElement(
        'pollAuthKey',
        'Truhenschluessel : '
      )

      var pollCheckboxes = createCheckboxes(pollOptions)

      var submitButton = createButtonElement('absenden', 'absenden', 'Absenden')

      removeHtmlContent(rootContainer)
      appendElements(
        rootContainer,
        [pollAuthLabel, pollAuthElement]
          .concat(pollCheckboxes)
          .concat([submitButton])
      )

      return {
        submitButton: submitButton,
        checkboxes: pollCheckboxes,
        pollAuthElement: pollAuthElement
      }
    })

    function getPollOptions (pollData) {
      return pollData.items.map(function (pollItem) {
        return pollItem.name
      })
    }
    function createInputElement () {
      return document.createElement('input')
    }
    function createTextInputElement (id, name) {
      var textInputElement = createInputElement()
      textInputElement.type = 'text'
      textInputElement.id = id
      textInputElement.name = name
      return textInputElement
    }
    function createCheckboxElement (id, name, value) {
      var checkbox = createInputElement()

      checkbox.type = 'checkbox'
      checkbox.id = id
      checkbox.name = name
      checkbox.value = value

      return checkbox
    }
    function createLabelElement (htmlFor, text) {
      var label = document.createElement('label')
      label.htmlFor = htmlFor
      label.appendChild(document.createTextNode(text))
      return label
    }
    function createButtonElement (id, name, text) {
      var button = document.createElement('button')
      button.id = id
      button.name = name
      button.appendChild(document.createTextNode(text))
      return button
    }
    function createCheckboxes (options) {
      return options.map(function (option) {
        var normalizedOption = replaceSpaceWithDash(option)

        var checkbox = createCheckboxElement(
          normalizedOption,
          normalizedOption,
          option
        )

        var label = applyStandardPadding(
          createLabelElement(normalizedOption, option)
        )

        return dropElementsIntoContainer([checkbox, label])
      })
    }
    function dropElementsIntoContainer (elements) {
      var container = document.createElement('div')
      appendElements(container, elements)
      return container
    }
    function appendElements (element, elements) {
      elements.forEach(function (child) {
        element.appendChild(child)
      })
    }
    function applyStandardPadding (element) {
      element.className = 'padded'
      return element
    }
    function replaceSpaceWithDash (item) {
      return item.toLowerCase().replace(' ', '-')
    }
    function removeHtmlContent (element) {
      element.innerHTML = ''
    }
  })(database)

  // updates module
  ;(function (database, render) {
    render
      .then(function (renderedElements) {
        var checkboxes = getCheckboxesFromTheirContainer(
          renderedElements.checkboxes
        )
        renderedElements.submitButton.onclick = sumbitButtonClicked(
          checkboxes,
          renderedElements.pollAuthElement
        )
      })
      .catch(function () {
        alert(
          'Die Daten fuer die Abstimmung konnten nicht geladen werden, ist deine Internetverbindung ok ?'
        )
      })

    function sumbitButtonClicked (checkboxes, pollAuthElement) {
      return function () {
        database
          .getCurrentPoll()
          .once('value', function (snapshot) {
            var currentPollData = snapshot.val()

            var voteCount = countVotes(checkboxes)
            var authKey = pollAuthElement.value
            if (
              validateVoteCounts(voteCount) &&
              validateAuthKeyLength(authKey) &&
              validateAuthKeyPermission(currentPollData, authKey)
            ) {
              var selectedVotes = getSelectedVotesByUser(checkboxes)
              var update = getUpdateBatchForInsertAuthKeyIntoSelectedVotes(
                currentPollData,
                selectedVotes,
                authKey
              )

              if (typeof update === 'object') {
                database.query().update(update, function (error) {
                  if (!error) {
                    alert('Deine Abstimmung war erfolgreich !')
                  } else {
                    alert(
                      'Deine Abstimmung war nicht erfolgreich, bitte versuche es spaeter nochmal !'
                    )
                  }
                })
              }
            }
          })
          .catch(function () {
            alert('Bitte prüfe deine Internetverbindung ...')
          })
      }
    }
    function getCheckboxesFromTheirContainer (containers) {
      return containers.map(function (checkboxCon) {
        var checkbox = checkboxCon.querySelector('input[type=checkbox]')
        return checkbox
      })
    }
    function countVotes (checkboxes) {
      return checkboxes.reduce(function (sum, checkbox) {
        return checkbox.checked ? sum + 1 : sum
      }, 0)
    }
    function validateVoteCounts (voteCount) {
      if (voteCount != 2) {
        alert(
          'Du hast zwei Stimmen ! Du hast aber ' +
            voteCount +
            ' checkboxen aktiviert.'
        )
        return false
      }
      return true
    }
    function validateAuthKeyLength (key) {
      if (key.length != 16) {
        alert(
          'Dein Truhenschluessel muss exakt 16 Zeichen haben, aktuell hast du ' +
            key.length +
            ' Zeichen.'
        )
        return false
      }
      return true
    }
    function validateAuthKeyPermission (pollData, authKey) {
      var validKey = lookupInAuthKeys(pollData, function (currentAuthKey) {
        return currentAuthKey === authKey
      })
      var keyVotePermission = lookupInVotes(pollData, function (
        consumendAuthKey
      ) {
        return consumendAuthKey !== authKey
      })

      if (!validKey || !keyVotePermission) {
        alert('Dein Truhenschluessel ist ungueltig oder wurde schon benutzt !')
        return false
      }

      return true
    }
    function lookupInAuthKeys (pollData, lookup) {
      return pollData.keys.some(function (currentAuthKey) {
        return lookup(currentAuthKey.value)
      })
    }
    function lookupInVotes (pollData, lookup) {
      return pollData.items.every(function (item) {
        return Object.keys(item.votes).every(function (voteInstanceProp) {
          return lookup(item.votes[voteInstanceProp])
        })
      })
    }
    function getSelectedVotesByUser (checkboxes) {
      return checkboxes.reduce(function (votes, checkbox) {
        return checkbox.checked ? votes.concat([checkbox.value]) : votes
      }, [])
    }
    function getUpdateBatchForInsertAuthKeyIntoSelectedVotes (
      pollData,
      selectedVotes,
      authKey
    ) {
      var update = {}
      selectedVotes.forEach(function (vote) {
        var dbVoteIndex = getDbIndexOfVote(pollData, vote)
        var insertKey = database.getInsertKey(
          'polls/0/items/' + dbVoteIndex + '/votes'
        )

        update['polls/0/items/' + dbVoteIndex + '/votes/' + insertKey] = authKey
      })

      return update
    }
    function getDbIndexOfVote (pollData, voteName) {
      var dbVoteIndex = -1
      pollData.items.some(function (dbVoteItem) {
        dbVoteIndex += 1
        if (dbVoteItem.name === voteName) {
          return true
        }
      })
      return dbVoteIndex
    }
  })(database, render)
}
