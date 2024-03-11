
document.addEventListener('DOMContentLoaded', function() {

    var micButton = document.getElementById('micButton');

    const voiceResponseDiv = document.getElementById('voiceResponse'); 

    // const waitTimeDiv = document.getElementById('waitingTime');
    
    // // Function to update the wait time display
    // function updateWaitTime() {
    //     fetch('/estimated_wait_time')
    //         .then(response => {
    //             if (!response.ok) {
    //                 throw new Error(`HTTP error! status: ${response.status}`);
    //             }
    //             return response.json();
    //         })
    //         .then(data => {
    //             console.log('Wait Time Data:', data); // Debugging output
    //             waitTimeDiv.textContent = `Estimated Wait Time: ${data.waitTime} minutes`;
    //         })
    //         .catch(error => {
    //             console.error('Error fetching wait time:', error);
    //             waitTimeDiv.textContent = "Error retrieving wait time.";
    //         });
    // }
    
    // // Periodically update the wait time every minute
    // setInterval(updateWaitTime, 60000);
    // updateWaitTime(); // Initial update on page load

    micButton.addEventListener('click', function() {
        this.classList.toggle('recording');
            fetch('/voice_checkin') // Adjust the endpoint as necessary
                .then(response => response.json())
                .then(data => {
                    if (data.checkInConfirmed && data.orderComponents) {
                        // Create elements for displaying order details
                        const orderDetailsDiv = document.createElement('div');
                        orderDetailsDiv.className = 'order-details';
                
                        const heading = document.createElement('h2');
                        heading.textContent = 'Order Confirmation';
                        orderDetailsDiv.appendChild(heading);
                
                        // Dynamically creating and appending details to orderDetailsDiv
                        const summaryParagraph = document.createElement('p');
                        summaryParagraph.innerHTML = `<strong>Order Summary:</strong> ${data.orderComponents.orderSummary || 'Not provided'}`;
                        orderDetailsDiv.appendChild(summaryParagraph);
                
                        const priceParagraph = document.createElement('p');
                        priceParagraph.innerHTML = `<strong>Total Price:</strong> $${data.orderComponents.totalPrice || 'Not provided'}`;
                        orderDetailsDiv.appendChild(priceParagraph);
        
                        // Append the orderDetailsDiv to an existing element in your page, such as the check-in container
                        document.querySelector('.check-in-container').innerHTML = ''; // Clear any existing content
                        document.querySelector('.check-in-container').appendChild(orderDetailsDiv);
        
                        // Handle message display
                        if(data.message) {
                            voiceResponseDiv.innerText = data.message; // Update with any message if present
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    voiceResponseDiv.innerText = "Error in processing the request."; // Display an error message
                });
        }
    );
    

    

        
    document.getElementById('micButton').addEventListener('click', function() {
        this.classList.toggle('recording');
    });
    });
    


 
    let mediaRecorder;
    let audioChunks = [];
    
    document.getElementById('micButton').addEventListener('mousedown', function() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                mediaRecorder.start();
            });
    });
    
    document.getElementById('micButton').addEventListener('mouseup', function() {
        if (mediaRecorder) {
            mediaRecorder.stop();
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                sendAudioToServer(audioBlob).then(() => {
                    fetch('/voice_checkin') // Adjust the endpoint as necessary
                        .then(response => response.json())
                        .then(data => {
                            // Handle the response data here
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
                audioChunks = [];
            };
        }
    });
    
    // Assuming you have the recording logic in place as shown in your original script

    function sendAudioToServer(audioBlob) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.wav');
            
            fetch('/upload_audio', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if(data.audioUrl) {
                    const audio = new Audio(data.audioUrl);
                    audio.play();
                }
                console.log(data.message); // Log the response message from Flask
                resolve(); // Resolve the promise
            })
            .catch(error => {
                console.log('Error:', error);
                reject(error); // Reject the promise
            });
        });
    }
    $('.product-image--list li').hover(function() {
        var url = $(this).children('img').attr('src');
        $('.item-selected').removeClass('item-selected');
        $(this).addClass('item-selected');
        $('#featured').attr('src', url);
      });
      
      $('#buy-toaster').click(function() {
        alert("BUY ME PLS!");
      });